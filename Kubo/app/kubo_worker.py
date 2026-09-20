"""Local RVC subprocess: length-prefixed PCM24k in and out, stdout is binary only."""
import os
import sys
import struct
import tempfile
from pathlib import Path


def read_exact(stream, size):
    data = bytearray()
    while len(data) < size:
        part = stream.read(size - len(data))
        if not part:
            raise EOFError('RVC pipe closed')
        data.extend(part)
    return bytes(data)


def main():
    pipe = sys.stdout.buffer
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    sys.stdout = sys.stderr

    # Determine paths: release bundle vs source workspace
    cur = Path(__file__).resolve().parent
    env_models = os.environ.get('KUBO_MODELS_DIR')
    models_dir = None
    rvc = cur

    if env_models and Path(env_models).is_dir():
        models_dir = Path(env_models).resolve()
    else:
        for ancestor in (cur, *cur.parents):
            candidate = ancestor / 'data' / 'models'
            if candidate.is_dir():
                models_dir = candidate.resolve()
                break

    if models_dir is None:
        root = Path(__file__).resolve().parents[2]
        rvc = root / 'work/rvc'

    if models_dir is not None:
        weight_root = str(models_dir)
        index_root = str(models_dir)
        outside_index_root = str(models_dir)
        rmvpe_root = str(models_dir)
        hubert_path = str(models_dir / 'hubert_base')
        local_app = os.environ.get('LOCALAPPDATA')
        base_cache = Path(local_app) if local_app else Path.home() / 'AppData' / 'Local'
        mpl_cache = str(base_cache / 'Kubo' / 'cache' / 'mpl')
    else:
        weight_root = str(rvc / 'assets/weights')
        index_root = str(rvc / 'logs')
        outside_index_root = str(rvc / 'assets/indices')
        rmvpe_root = str(rvc / 'assets/rmvpe')
        hubert_path = str(rvc / 'assets/hubert_base')
        mpl_cache = str(Path(tempfile.gettempdir()) / 'kubo-mpl-cache')

    Path(mpl_cache).mkdir(parents=True, exist_ok=True)
    os.chdir(rvc)
    sys.path.insert(0, str(rvc))
    sys.argv = [sys.argv[0]]
    os.environ.update(
        weight_root=weight_root,
        index_root=index_root,
        outside_index_root=outside_index_root,
        rmvpe_root=rmvpe_root,
        RVC_HUBERT_PATH=hubert_path,
        OMP_NUM_THREADS='4',
        RVC_CUDA_GRAPH='0',
        MPLCONFIGDIR=mpl_cache,
    )
    bin_dirs = [str(rvc), str(rvc.parent / 'bin')]
    for bd in bin_dirs:
        if Path(bd).is_dir():
            os.environ['PATH'] = bd + os.pathsep + os.environ['PATH']

    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from configs.config import Config
    from infer.vc.modules import VC
    from infer.vc.utils import get_index_path_from_model

    # Validate essential models before initialization
    model = 'NagisaKubo_e300_s1500.pth'
    weight_file = Path(weight_root) / model
    if not weight_file.is_file():
        raise FileNotFoundError(f'Không tìm thấy trọng số model RVC Nagisa Kubo: {weight_file}. Xem hướng dẫn tại docs/ASSETS.md.')

    rmvpe_file = Path(rmvpe_root) / 'rmvpe.pt'
    if not rmvpe_file.is_file():
        raise FileNotFoundError(f'Không tìm thấy trọng số RMVPE: {rmvpe_file}. Xem hướng dẫn tại docs/ASSETS.md.')

    hubert_cfg = Path(hubert_path) / 'config.json'
    if not hubert_cfg.is_file():
        raise FileNotFoundError(f'Không tìm thấy cấu hình HuBERT: {hubert_cfg}. Xem hướng dẫn tại docs/ASSETS.md.')

    vc = VC(Config())
    index = get_index_path_from_model(model, 0)
    if not index or not Path(index).is_file():
        raise FileNotFoundError(f'Không tìm thấy file index RVC cho Nagisa Kubo: {index}. Xem hướng dẫn tại docs/ASSETS.md.')
    vc.get_vc(model)
    # Warm up feature and pitch models before reporting readiness.
    with tempfile.TemporaryDirectory(prefix='kubo-') as tmp:
        source = Path(tmp)/'input.wav'
        def convert(pcm):
            x = np.frombuffer(pcm, dtype='<i2').astype(np.float32)/32768
            original = len(x)
            x = np.pad(x, (2400, 2400 + max(0, 24000-len(x))))
            sf.write(source, x, 24000)
            status, result = vc.vc_single(0, str(source), 6, 'rmvpe', index, .75, 24000, .25, .33)
            if result is None or result[1] is None:
                raise RuntimeError(status)
            rate, data = result
            y = data.astype(np.float32)
            if np.issubdtype(data.dtype, np.integer):
                y /= 32768
            if rate != 24000:
                import math
                divisor = math.gcd(rate, 24000)
                y = resample_poly(y, 24000//divisor, rate//divisor)
            y = y[2400:2400+original]
            y = np.pad(y, (0, max(0, original-len(y))))
            if not np.isfinite(y).all():
                raise ValueError('Non-finite RVC output')
            # Brief edge fades suppress clicks at independently converted boundaries.
            edge = min(120, len(y)//2)
            if edge:
                y[:edge] *= np.linspace(0, 1, edge)
                y[-edge:] *= np.linspace(1, 0, edge)
            return (np.clip(y, -1, 1)*32767).astype('<i2').tobytes()
        convert(bytes(48000))
        pipe.write(b'READY'); pipe.flush()
        while True:
            try:
                size = struct.unpack('<I', read_exact(sys.stdin.buffer, 4))[0]
            except EOFError:
                return
            if size < 2 or size > 24000*2*10 or size % 2:
                raise ValueError('Invalid PCM input size')
            output = convert(read_exact(sys.stdin.buffer, size))
            pipe.write(struct.pack('<I', len(output)) + output); pipe.flush()


if __name__ == '__main__':
    main()

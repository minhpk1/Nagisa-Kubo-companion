#include <windows.h>
#include <stdio.h>
#include <wchar.h>

int wmain(int argc, wchar_t* argv[]) {
    // 1. Get directory where KuboVoice.exe is located
    wchar_t exePath[MAX_PATH];
    if (GetModuleFileNameW(NULL, exePath, MAX_PATH) == 0) {
        fwprintf(stderr, L"KuboVoice: Cannot get module file name\n");
        return 1;
    }
    wchar_t* lastSlash = wcsrchr(exePath, L'\\');
    if (lastSlash) {
        *lastSlash = L'\0';
    }

    // 2. Construct paths to runtime\python.exe and engine\kubo_worker.py
    wchar_t pythonExe[MAX_PATH];
    wchar_t workerPy[MAX_PATH];
    wchar_t engineDir[MAX_PATH];
    swprintf_s(pythonExe, MAX_PATH, L"%s\\runtime\\python.exe", exePath);
    swprintf_s(workerPy, MAX_PATH, L"%s\\engine\\kubo_worker.py", exePath);
    swprintf_s(engineDir, MAX_PATH, L"%s\\engine", exePath);

    // 3. Build command line: "runtime\python.exe" -u "engine\kubo_worker.py"
    wchar_t cmdLine[MAX_PATH * 3];
    swprintf_s(cmdLine, MAX_PATH * 3, L"\"%s\" -u \"%s\"", pythonExe, workerPy);

    // 4. Forward std handles for length-prefixed PCM binary pipe
    STARTUPINFOW si;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);

    PROCESS_INFORMATION pi;
    ZeroMemory(&pi, sizeof(pi));

    // 5. Clean environment to prevent PyInstaller or outer venv leakage
    SetEnvironmentVariableW(L"PYTHONSAFEPATH", L"1");
    SetEnvironmentVariableW(L"PYTHONPATH", NULL);
    SetEnvironmentVariableW(L"PYTHONHOME", NULL);
    SetEnvironmentVariableW(L"_MEIPASS", NULL);
    SetEnvironmentVariableW(L"_MEIPASS2", NULL);

    // 6. Create Job Object to ensure child Python process is terminated if launcher dies
    HANDLE hJob = CreateJobObjectW(NULL, NULL);
    if (hJob != NULL) {
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION jeli;
        ZeroMemory(&jeli, sizeof(jeli));
        jeli.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        SetInformationJobObject(hJob, JobObjectExtendedLimitInformation, &jeli, sizeof(jeli));
    }

    // 7. Launch worker subprocess suspended, assign to job, then resume
    BOOL success = CreateProcessW(
        NULL,
        cmdLine,
        NULL,
        NULL,
        TRUE, // Inherit std handles
        CREATE_SUSPENDED,
        NULL,
        engineDir,
        &si,
        &pi
    );

    if (!success) {
        DWORD err = GetLastError();
        fwprintf(stderr, L"KuboVoice: Failed to start runtime (%lu)\n", err);
        if (hJob != NULL) {
            CloseHandle(hJob);
        }
        return (int)err;
    }

    if (hJob != NULL) {
        AssignProcessToJobObject(hJob, pi.hProcess);
    }
    ResumeThread(pi.hThread);

    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD exitCode = 0;
    GetExitCodeProcess(pi.hProcess, &exitCode);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    if (hJob != NULL) {
        CloseHandle(hJob);
    }
    return (int)exitCode;
}

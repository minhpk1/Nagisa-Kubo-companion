import asyncio
import json
import tempfile
import threading
import unittest
from pathlib import Path
from agent_tools import LocalTools
from agent_session import AgentSession
from protocol import start_event
from live_client import run_session
from test_companion import Socket, FakeAudio

class LocalToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.root=self.base/'allowed';self.root.mkdir()
        (self.root/'voice').mkdir()
        (self.root/'note.txt').write_text('Xin chào Kubo',encoding='utf-8')
        (self.root/'.env').write_text('SECRET=hidden')
        (self.base/'outside.txt').write_text('outside')
        self.opened=[]
        self.tools=LocalTools([self.root],opener=self.opened.append)

    def tearDown(self): self.tmp.cleanup()

    def test_read_search_and_open_real_allowed_files(self):
        self.assertEqual(self.tools.execute('read_text',{'root_id':'root0','path':'note.txt'})['content'],'Xin chào Kubo')
        self.assertEqual(self.tools.execute('find_files',{'root_id':'root0','query':'note'})['files'],['note.txt'])
        result=self.tools.execute('open_folder',{'root_id':'root0','path':'voice'})
        self.assertTrue(result['ok']);self.assertEqual(self.opened,[str(self.root/'voice')])
        listed=self.tools.execute('list_folder',{'root_id':'root0','path':'.'})
        self.assertNotIn('.env',[x['path'] for x in listed['items']])

    def test_boundaries_and_no_arbitrary_execution(self):
        for path in ['../outside.txt','.env','note.txt:stream','C:/Windows','\\\\server\\share']:
            self.assertFalse(self.tools.execute('read_text',{'root_id':'root0','path':path})['ok'],path)
        self.assertFalse(self.tools.execute('open_folder',{'root_id':'root0','path':'note.txt'})['ok'])
        self.assertFalse(self.tools.execute('run_shell',{'command':'anything'})['ok'])
        self.assertFalse(self.tools.execute('read_text','bad json')['ok'])
        self.assertFalse(self.tools.execute('list_folder',{'root_id':'root9','path':'.'})['ok'])
        self.assertEqual(self.opened,[])
        self.assertEqual(LocalTools([]).execute('list_roots',{})['roots'],[])

    def test_frozen_empty_settings_default_roots(self):
        import paths
        from unittest.mock import patch
        with patch.object(paths, 'is_frozen', return_value=True):
            self.assertEqual(paths.get_default_allowed_roots(), [])
            tools = LocalTools(roots=None)
            self.assertEqual(tools.roots, [])
            self.assertEqual(tools.execute('list_roots', {})['roots'], [])
            self.assertFalse(tools.execute('read_text', {'root_id': 'root0', 'path': 'note.txt'})['ok'])
            self.assertFalse(tools.execute('find_files', {'root_id': 'root0', 'query': 'note'})['ok'])


    def test_symlink_escape(self):
        link=self.root/'escape.txt'
        try: link.symlink_to(self.base/'outside.txt')
        except OSError: self.skipTest('Windows account cannot create symlinks')
        self.assertFalse(self.tools.execute('read_text',{'root_id':'root0','path':'escape.txt'})['ok'])
        self.assertFalse(self.tools.execute('open_file',{'root_id':'root0','path':'escape.txt'})['ok'])

    def test_open_file_types_and_unicode_path(self):
        for name in ['Tài liệu có dấu.PDF','ảnh.png','report.docx','clip.mp4','page.html','track.mp3']:
            (self.root/name).write_bytes(b'test')
            result=self.tools.execute('open_file',{'root_id':'root0','path':name})
            self.assertTrue(result['ok'],result)
            self.assertEqual(result['status'],'launch_requested')
            self.assertEqual(self.opened[-1],str(self.root/name))
        self.assertIn('open_file',[t['name'] for t in start_event(agent_enabled=True)['session']['delegation']['responses']['tools']])

    def test_open_file_rejections_and_launch_error(self):
        for name in ['run.exe','shortcut.lnk','link.url','picture.jpg.exe','macro.docm']:
            (self.root/name).write_bytes(b'test')
            self.assertFalse(self.tools.execute('open_file',{'root_id':'root0','path':name})['ok'])
        for name in ['../outside.txt','voice','missing.pdf','.env','note.txt:stream']:
            self.assertFalse(self.tools.execute('open_file',{'root_id':'root0','path':name})['ok'])
        self.assertEqual(self.opened,[])
        def fail(path): raise OSError('No associated application')
        self.tools.opener=fail
        self.assertFalse(self.tools.execute('open_file',{'root_id':'root0','path':'note.txt'})['ok'])

    def test_code_opens_in_editor_without_executing_source(self):
        editor=self.base/'Editor with spaces.exe';editor.write_bytes(b'test stub')
        launched=[]
        self.tools.editor=str(editor)
        self.tools.launcher=lambda args,**kwargs: launched.append((args,kwargs))
        for name in ['Bài tập.cpp','run.py','run.ps1','run.cmd','app.tsx']:
            (self.root/name).write_text('sample source',encoding='utf-8')
            self.assertTrue(self.tools.execute('open_file',{'root_id':'root0','path':name})['ok'])
            self.assertEqual(launched[-1],([str(editor),str(self.root/name)],{'shell':False,'cwd':str(self.base)}))
            self.assertEqual(self.tools.execute('read_text',{'root_id':'root0','path':name})['content'],'sample source')
        self.assertEqual(self.opened,[])
        self.tools.editor=str(self.base/'missing.exe')
        self.assertFalse(self.tools.execute('open_file',{'root_id':'root0','path':'Bài tập.cpp'})['ok'])
        self.assertEqual(len(launched),5)

    def test_only_configured_apps_launch_with_no_model_arguments(self):
        executable=self.base/'Approved.exe';executable.write_bytes(b'test stub')
        launched=[]
        tools=LocalTools([],apps=[{'name':'Approved','path':str(executable)}],launcher=lambda args,**kw:launched.append((args,kw)))
        self.assertEqual(tools.execute('list_apps',{})['apps'],[{'app_id':'app0','name':'Approved','available':True}])
        for args in [{'app_id':'app1'},{'app_id':'app-1'},{'app_id':str(executable)},
                     {'app_id':'app0','arguments':'anything'}]:
            self.assertFalse(tools.execute('open_app',args)['ok'])
        self.assertEqual(launched,[])
        self.assertTrue(tools.execute('open_app',{'app_id':'app0'})['ok'])
        self.assertEqual(launched,[([str(executable)],{'shell':False,'cwd':str(self.base)})])
        tools.stop.set()
        self.assertFalse(tools.execute('open_app',{'app_id':'app0'})['ok'])
        self.assertEqual(len(launched),1)
        self.assertEqual(LocalTools([],apps=[]).execute('list_apps',{})['apps'],[])
        executable.unlink();tools.stop.clear()
        self.assertFalse(tools.execute('open_app',{'app_id':'app0'})['ok'])
        definitions=start_event(agent_enabled=True)['session']['delegation']['responses']['tools']
        self.assertTrue({'list_apps','open_app'} <= {t['name'] for t in definitions})

    def test_read_limit_and_cancel(self):
        (self.root/'long.txt').write_text('a'*70000)
        result=self.tools.execute('read_text',{'root_id':'root0','path':'long.txt'})
        self.assertTrue(result['truncated']);self.assertEqual(len(result['content']),65536)
        self.tools.stop.set()
        self.assertFalse(self.tools.execute('open_folder',{'root_id':'root0','path':'.'})['ok'])
        self.assertEqual(self.opened,[])

    def test_ui_ack_not_fabricated(self):
        (self.root/'clip.wav').write_bytes(b'RIFF')
        def ui(request):
            request['result']={'ok':False,'error':'Invalid WAV'};request['done'].set()
        tools=LocalTools([self.root],ui=ui)
        self.assertFalse(tools.execute('play_audio',{'root_id':'root0','path':'clip.wav'})['ok'])

class AgentFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_stop_cancels_pending_work_without_result(self):
        tools=LocalTools([])
        agent=AgentSession(tools,lambda x:None)
        tools.stop.set()
        await agent.execute([{'call_id':'c','name':'list_roots','arguments':'{}'}])
        self.assertTrue(agent.outbox.empty())

    async def test_backend_error_is_not_mistaken_for_user_stop(self):
        tools=LocalTools([])
        agent=AgentSession(tools,lambda x:None)
        ws,audio,stop=Socket(),FakeAudio(),threading.Event()
        ws.feed({'type':'session.started'})
        ws.feed({'type':'error','error':{'message':'backend denied'}})
        with self.assertRaisesRegex(RuntimeError,'backend denied'):
            await run_session(ws,audio,stop,threading.Event(),lambda *x:None,{'agent_enabled':True},agent=agent)
        self.assertFalse(stop.is_set())
        self.assertTrue(tools.stop.is_set())

    async def test_full_fake_socket_roundtrip_and_no_duplicate(self):
        tools=LocalTools([])
        agent=AgentSession(tools,lambda x:None)
        ws,audio,stop=Socket(),FakeAudio(),tools.stop
        ws.feed({'type':'session.started'})
        def feed(event): ws.feed({'type':'response.event','delegation_id':'d1','event':event})
        feed({'type':'response.created','response':{'id':'r1'}})
        item={'type':'function_call','call_id':'c1','name':'list_roots','arguments':'{}'}
        feed({'type':'response.output_item.done','item':item})
        feed({'type':'response.output_item.done','item':item})
        task=asyncio.create_task(run_session(ws,audio,stop,threading.Event(),lambda *x:None,{'agent_enabled':True},agent=agent))
        await asyncio.sleep(.05)
        self.assertFalse(any(e['type']=='response.item.create' for e in ws.sent))
        feed({'type':'response.completed','response':{'id':'r1','output':[]}})
        for _ in range(60):
            if any(e['type']=='response.create' for e in ws.sent): break
            await asyncio.sleep(.01)
        results=[e for e in ws.sent if e['type']=='response.item.create']
        self.assertEqual(len(results),1)
        self.assertEqual(json.loads(results[0]['item']['output']),{'ok':True,'roots':[]})
        self.assertIn('tools',ws.sent[0]['session']['delegation']['responses'])
        feed({'type':'response.output_item.done','response_id':'r1','item':item})
        feed({'type':'response.completed','response':{'id':'r1','output':[]}})
        await asyncio.sleep(.04)
        self.assertEqual(len([e for e in ws.sent if e['type']=='response.item.create']),1)
        stop.set();await asyncio.wait_for(task,1)

    async def test_failed_response_never_executes_and_disabled_tools_absent(self):
        tools=LocalTools([])
        agent=AgentSession(tools,lambda x:None)
        for event in [{'type':'response.created','response':{'id':'r'}},
                      {'type':'response.output_item.done','item':{'type':'function_call','call_id':'c','name':'list_roots','arguments':'{}'}},
                      {'type':'response.failed','response':{'id':'r'}}]:
            agent.event({'delegation_id':'d','event':event})
        await asyncio.sleep(.02)
        self.assertTrue(agent.outbox.empty())
        self.assertNotIn('tools',start_event(agent_enabled=False)['session']['delegation']['responses'])
        await agent.close()

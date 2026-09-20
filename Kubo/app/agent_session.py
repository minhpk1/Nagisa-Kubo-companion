"""Nonblocking bridge for completed GPT-Live Responses function calls."""
import asyncio
import json
import uuid

class AgentSession:
    def __init__(self, tools, notify):
        self.tools, self.notify = tools, notify
        self.responses = {}
        self.current = {}
        self.seen = set()
        self.tasks = set()
        self.outbox = asyncio.Queue()
        self.serial = asyncio.Lock()

    def event(self, envelope):
        event=envelope.get('event',{})
        delegation=envelope.get('delegation_id','')
        kind=event.get('type')
        if kind=='response.created':
            rid=event.get('response',{}).get('id')
            if rid:
                self.current[delegation]=rid
                self.responses.setdefault(rid,[])
        elif kind=='response.output_item.done':
            item=event.get('item',{})
            rid=event.get('response_id') or self.current.get(delegation)
            if rid and item.get('type')=='function_call' and item.get('call_id'):
                calls=self.responses.setdefault(rid,[])
                if not any(c['call_id']==item['call_id'] for c in calls): calls.append(item)
        elif kind=='response.completed':
            rid=event.get('response',{}).get('id') or self.current.get(delegation)
            calls=self.responses.pop(rid,[])
            if calls:
                task=asyncio.create_task(self.execute(calls))
                self.tasks.add(task);task.add_done_callback(self.tasks.discard)
        elif kind in ('response.failed','response.cancelled','response.incomplete'):
            rid=event.get('response',{}).get('id') or self.current.get(delegation)
            self.responses.pop(rid,None)
            self.notify('Tác vụ backend không hoàn tất; chưa chạy công cụ.')

    async def execute(self, calls):
        async with self.serial:
            sent=False
            for call in calls:
                cid=call['call_id']
                if cid in self.seen: continue
                self.seen.add(cid)
                if self.tools.stop.is_set(): return
                self.notify('Đang thực hiện: '+str(call.get('name','')))
                if len(self.seen)>64:
                    result={'ok':False,'error':'Đã đạt giới hạn 64 lần gọi công cụ trong phiên.'}
                else:
                    try:
                        result=await asyncio.to_thread(self.tools.execute,call.get('name'),call.get('arguments','{}'))
                    except Exception:
                        result={'ok':False,'error':'Công cụ gặp lỗi nội bộ.'}
                if self.tools.stop.is_set(): return
                self.notify(('Hoàn tất: ' if result.get('ok') else 'Không thực hiện được: ')+str(call.get('name','')))
                await self.outbox.put({'type':'response.item.create','event_id':str(uuid.uuid4()),
                    'item':{'type':'function_call_output','call_id':cid,'output':json.dumps(result,ensure_ascii=False)}})
                sent=True
            if sent:
                await self.outbox.put({'type':'response.create','event_id':str(uuid.uuid4())})

    async def close(self):
        self.tools.stop.set()
        tasks=list(self.tasks)
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)

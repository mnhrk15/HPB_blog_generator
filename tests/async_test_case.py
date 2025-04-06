import asyncio
import unittest

class AsyncTestCase(unittest.TestCase):
    """非同期テストをサポートするためのテストケースクラス"""
    
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self._async_test_method = getattr(self, methodName)
        setattr(self, methodName, self._run_async_test)
    
    def _run_async_test(self):
        """非同期テストメソッドを実行するためのラッパーメソッド"""
        if asyncio.iscoroutinefunction(self._async_test_method):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._async_test_method())
            finally:
                loop.close()
        else:
            return self._async_test_method()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
import os
import asyncio
import inspect

# 非同期テストをサポートするカスタムテストランナー
class AsyncTestRunner(unittest.TextTestRunner):
    def run(self, test):
        """Run the given test case or test suite."""
        result = self._makeResult()
        result.failfast = self.failfast
        result.buffer = self.buffer
        result.tb_locals = self.tb_locals
        
        # テストを実行する前に、非同期メソッドをラップする
        self._wrap_async_methods(test)
        
        # 通常のテスト実行
        result.startTestRun()
        try:
            test(result)
        finally:
            result.stopTestRun()
        return result
    
    def _wrap_async_methods(self, test):
        """Wrap async test methods to run in the event loop."""
        if isinstance(test, unittest.TestCase):
            for attr in dir(test):
                if attr.startswith('test_'):
                    method = getattr(test, attr)
                    if inspect.iscoroutinefunction(method):
                        setattr(test, attr, self._wrap_async_method(method))
        else:
            # テストスイートの場合、再帰的に処理
            try:
                for subtest in test:
                    self._wrap_async_methods(subtest)
            except TypeError:
                pass
    
    def _wrap_async_method(self, method):
        """Wrap an async test method to run in the event loop."""
        def wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(method(*args, **kwargs))
            finally:
                loop.close()
        return wrapper

def run_tests():
    """すべてのテストを実行する"""
    # テストディレクトリのパスを取得
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    
    # テストローダーを作成
    loader = unittest.TestLoader()
    
    # ユニットテストとインテグレーションテストを検出
    unit_tests = loader.discover(os.path.join(test_dir, 'unit'), pattern='test_*.py')
    integration_tests = loader.discover(os.path.join(test_dir, 'integration'), pattern='test_*.py')
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    test_suite.addTests(unit_tests)
    test_suite.addTests(integration_tests)
    
    # カスタムテストランナーを作成して実行
    runner = AsyncTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果に基づいて終了コードを設定
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())

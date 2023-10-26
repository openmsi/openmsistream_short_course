"""Testing controlled processes"""

import unittest
import asyncio
from controlled_process_async import ControlledProcessAsync

# some constants
TIMEOUT_SECS = 10


class ControlledProcessAsyncForTesting(ControlledProcessAsync):
    """
    Class to use in testing ControlledProcessAsync
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.checked = False
        self.on_shutdown_called = False
        self.post_run_called = False

    async def run_task(self):
        while self.alive:
            if self.counter < 5:
                self.counter += 1
            await asyncio.sleep(1)

    def _on_check(self):
        self.checked = True

    def _on_shutdown(self):
        self.on_shutdown_called = True

    async def _post_run(self):
        self.post_run_called = True


class TestControlledProcess(unittest.TestCase):
    """
    Class for testing ControlledProcess utility classes
    """

    async def async_test_assertions(self, controlled_process, stop_event):
        """Make the assertions necessary to test the async controlled process"""
        await asyncio.sleep(1)
        await controlled_process.control_command_queue.put("c")
        await controlled_process.control_command_queue.put("check")
        await asyncio.sleep(1)
        self.assertTrue(controlled_process.checked)
        self.assertFalse(controlled_process.on_shutdown_called)
        self.assertFalse(controlled_process.post_run_called)
        await controlled_process.control_command_queue.put("q")
        await asyncio.sleep(2.0)
        self.assertTrue(controlled_process.on_shutdown_called)
        self.assertTrue(controlled_process.post_run_called)
        stop_event.set()

    async def run_async_tests(self, controlled_process):
        """Gather the controlled process's run loop and the test assertions, along
        with a timeout
        """
        stop_event = asyncio.Event()
        await asyncio.gather(
            controlled_process.run_loop(),
            self.async_test_assertions(controlled_process, stop_event),
            stop_event.wait(),
        )

    def test_controlled_process_async(self):
        """
        Test the async controlled process
        """
        cpa = ControlledProcessAsyncForTesting(update_secs=5)
        self.assertEqual(cpa.counter, 0)
        asyncio.run(
            asyncio.wait_for(self.run_async_tests(cpa), timeout=TIMEOUT_SECS),
        )

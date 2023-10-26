"""A process that can run async methods while waiting for user input to check
progress/status or shut it down
"""

# imports
import sys
import select
import asyncio
from abc import ABC, abstractmethod
from openmsitoolbox import LogOwner, OpenMSIArgumentParser


class ControlledProcessAsync(LogOwner, ABC):
    """
    A class to use when running async processes that should remain active until they are
    explicitly shut down

    :param update_secs: number of seconds to wait between printing a progress character
        to the console to indicate the program is alive
    :type update_secs: int, optional
    """

    #################### PROPERTIES ####################

    @property
    def alive(self):
        """
        Read-only boolean indicating if the process is running
        """
        return self.__alive

    #################### PUBLIC FUNCTIONS ####################

    def __init__(
        self,
        *args,
        update_secs: int = OpenMSIArgumentParser.DEF_UPDATE_SECS,
        **other_kwargs
    ):
        self.__update_secs = update_secs
        # a variable to indicate if the process has been shut down yet
        self.__alive = False
        # an asyncio process lock to guarantee exclusivity if necessary
        self.lock = asyncio.Lock()
        self.control_command_queue = None
        super().__init__(*args, **other_kwargs)

    async def run_loop(self):
        """Concurrently get user input, process user input, print the "still alive"
        character, and run the "run" function until the process is shut down. This
        is the main function that child classes should call.
        """
        self.__alive = True
        # start up a Queue that will hold the control commands
        self.control_command_queue = asyncio.Queue()
        tasks = [
            asyncio.create_task(self._add_user_input()),
            asyncio.create_task(self._handle_control_commands()),
            asyncio.create_task(self._print_still_alive()),
            asyncio.create_task(self.run_task()),
        ]
        while self.__alive:
            await asyncio.sleep(1)
        for task in tasks:
            task.cancel()
        await self._post_run()

    def shutdown(self):
        """
        Stop the process running.
        """
        self.__alive = False
        self._on_shutdown()

    #################### PRIVATE HELPER FUNCTIONS ####################

    async def _add_user_input(self):
        """
        Listen for and add user input to a queue at one second intervals
        """
        while self.__alive:
            await asyncio.sleep(1)
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
            if rlist!=[]:
                await self.control_command_queue.put((sys.stdin.read(1)).strip())

    async def _print_still_alive(self):
        # print the "still alive" character
        if self.__update_secs == -1:
            return
        while self.__alive:
            await asyncio.sleep(self.__update_secs)
            self.logger.debug(".")

    async def _handle_control_commands(self):
        while self.__alive:
            # get anything from the control command queue
            cmd = await self.control_command_queue.get()
            if cmd is not None:
                if cmd.lower() in ("q", "quit"):  # shut down the process
                    self.shutdown()
                elif cmd.lower() in ("c", "check"):  # run the on_check function
                    self._on_check()
                # otherwise just skip this unrecognized command

    async def _post_run(self):
        """This function is called after all the tasks have been shut down, to perform
        any final cleanup.

        Does nothing in the base class
        """
        return

    #################### ABSTRACT METHODS ####################

    @abstractmethod
    async def run_task(self) -> None:
        """
        Classes extending this base class should include the logic of actually
        running the controlled process in this function. It should include a
        "while self.alive" loop if it should run indefinitely, and "self.lock"
        can be acquired to guarantee exclusivity if necessary.

        Not implemented in the base class
        """
        raise NotImplementedError

    @abstractmethod
    def _on_check(self) -> None:
        """
        This function is run when the "check" command is found in the control queue.

        Not implemented in the base class
        """
        raise NotImplementedError

    @abstractmethod
    def _on_shutdown(self) -> None:
        """
        This function is run when the process is stopped; it's called from :func:`~shutdown`.

        Not implemented in the base class
        """
        raise NotImplementedError

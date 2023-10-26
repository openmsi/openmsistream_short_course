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
        character, and run the "run" function until the process is shut down
        """
        self.__alive = True
        # start up a Queue that will hold the control commands
        self.control_command_queue = asyncio.Queue()
        await asyncio.gather(
            self._add_user_input(),
            self._handle_control_commands(),
            self._print_still_alive(),
            self.run(),
        )

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
        if not sys.stdin.isatty:
            return
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

    async def _handle_control_commands(self) -> None:
        while self.__alive:
            # get anything from the control command queue
            cmd = await self.control_command_queue.get()
            if cmd is not None:
                if cmd.lower() in ("q", "quit"):  # shut down the process
                    self.shutdown()
                elif cmd.lower() in ("c", "check"):  # run the on_check function
                    self._on_check()
                # otherwise just skip this unrecognized command

    #################### ABSTRACT METHODS ####################

    @abstractmethod
    async def run(self) -> None:
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

import os
import asyncio
import argparse



from polar import Polar



def start_polar(address):
    """
    Start the Polar data collection.
    """
    polar_inst=Polar(address)
    # start the Polar data collection
    # polar(polar_address)
    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(polar_inst.main())


if __name__ == "__main__":
    # parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", type=str, default="00:22:D0:0B:3B:3B", help="MAC address of the Polar device")
    parser.add_argument("-lsl", "--lsl", type=bool, default=False, help="Send data to LSL")
    args = parser.parse_args()
    if args.lsl:
        # start the Polar data collection
        # Quick hack need to be fixed, in the package
        os.environ["LSL_STREAMING"] = str(1)
    else:
        os.environ["LSL_STREAMING"] = str(0)


    start_polar(args.address)

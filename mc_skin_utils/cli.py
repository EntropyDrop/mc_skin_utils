import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Minecraft Skin Utilities",
        usage="mc_skin_utils <command> [<args>]"
    )
    
    subcommands = {
        "mc_render": "Render a Minecraft skin in 3D using PyVista",
        "clean_skins": "Clean up artifact 'extra' pixels on skin images",
        "ensure_skin64x64": "Convert legacy 64x32 skins to modern 64x64 format"
    }
    
    parser.add_argument(
        "command", 
        choices=subcommands.keys(),
        help="Subcommand to run"
    )
    
    # Parse only the first argument as the command
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        # Format a nice help message
        print("usage: mc_skin_utils <command> [<args>]")
        print("\nMinecraft Skin Utilities\n\nAvailable commands:")
        for cmd, desc in subcommands.items():
            print(f"  {cmd:<20} {desc}")
        print("\nRun 'mc_skin_utils <command> --help' for more information on a specific command.")
        sys.exit(0 if len(sys.argv) > 1 else 1)
        
    args = parser.parse_args(sys.argv[1:2])
    
    if args.command == "mc_render":
        from . import mc_render
        sys.argv[0] = "mc_skin_utils mc_render"
        del sys.argv[1]
        mc_render.main()
    elif args.command == "clean_skins":
        from . import clean_skins_extra_pixels
        sys.argv[0] = "mc_skin_utils clean_skins"
        del sys.argv[1]
        clean_skins_extra_pixels.main()
    elif args.command == "ensure_skin64x64":
        from . import ensure_skin64x64
        sys.argv[0] = "mc_skin_utils ensure_skin64x64"
        del sys.argv[1]
        ensure_skin64x64.main()

if __name__ == '__main__':
    main()

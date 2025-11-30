import os
import sys
import shutil
import time
import ptyprocess
from pathlib import Path

def test_specify_init():
    """
    Simulates 'specify init' to test if we can automate the interactive prompts.
    """
    # 1. Create a temp directory for the test
    test_dir = Path(".specify_test_sandbox")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    print(f"--- Starting Simulation in {test_dir.absolute()} ---")
    
    # Change CWD to the test dir so 'specify init' runs there
    os.chdir(test_dir)

    try:
        # 2. Launch 'specify init' via ptyprocess
        # We use ptyprocess to mimic a real terminal
        # FIX: Must specify target directory ('.')
        cmd = "specify init ."
        print(f"Running: {cmd}")
        
        p = ptyprocess.PtyProcessUnicode.spawn(cmd.split())
        
        # 3. Handle Interaction Loop
        # We need to read stdout and look for prompts
        
        # READ 1: Wait for the AI selection prompt
        # We expect something like "Select an AI to use:"
        output = ""
        while True:
            try:
                chunk = p.read()
                output += chunk
                print(f"[STDOUT]: {chunk}", end="")
                
                # Check for common prompts (adjust based on real output)
                if "Select an AI" in output or "Select the AI" in output or "Claude" in output:
                    print("\n>>> Detected AI Prompt! Sending 'claude'...")
                    # In interactive lists, we might need down arrows or just typing the name?
                    # Let's try typing 'claude' and Enter. 
                    # If it's a arrow-key menu, we might need '\x1b[B' (down arrow)
                    # For now, assume text input or simple selection.
                    # Let's wait a split second for the menu to render
                    time.sleep(1)
                    p.write("claude\n")
                    output = "" # Reset buffer
                    break
            except EOFError:
                print("\n[EOF] Process ended prematurely.")
                break

        # READ 2: Wait for completion or next prompt
        while True:
            try:
                chunk = p.read()
                print(f"[STDOUT]: {chunk}", end="")
                if "Initialized" in chunk or "Success" in chunk or "created" in chunk:
                    print("\n>>> Detected Success!")
                    break
            except EOFError:
                break
                
        # 4. Verify Artifacts
        # Check if .specify directory exists
        if Path(".specify").exists():
            print("\n[PASS] .specify directory created!")
            return True
        else:
            print("\n[FAIL] .specify directory NOT found.")
            return False

    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False
    finally:
        p.close()
        # Cleanup (optional, maybe keep for inspection)
        # shutil.rmtree(test_dir)

if __name__ == "__main__":
    success = test_specify_init()
    sys.exit(0 if success else 1)

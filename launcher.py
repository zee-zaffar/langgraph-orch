#!/usr/bin/env python3
"""
LangGraph Chat Agent Launcher
Choose between console and web UI
"""

import subprocess
import sys
import os
from pathlib import Path

def run_console_version():
    """Run the console-based chat agent"""
    print("🚀 Starting Console Chat Agent...")
    try:
        subprocess.run([sys.executable, "graph-chat-agent.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Console chat agent stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running console version: {e}")

def run_streamlit_version():
    """Run the Streamlit web UI version"""
    print("🚀 Starting Streamlit Web UI...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Streamlit web UI stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit version: {e}")

def main():
    """Main launcher interface"""
    print("🤖 LangGraph Chat Agent Launcher")
    print("=" * 50)
    print("Choose your interface:")
    print("1. 💻 Console Chat (Terminal-based)")
    print("2. 🌐 Web UI (Streamlit)")
    print("3. ❌ Exit")
    print("=" * 50)
    
    while True:
        try:
            choice = input("\nEnter your choice (1, 2, or 3): ").strip()
            
            if choice == "1":
                run_console_version()
                break
            elif choice == "2":
                run_streamlit_version()
                break
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n👋 Launcher interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Change to script directory
    os.chdir(Path(__file__).parent)
    main()
"""
Enhanced WebSocket Real-time Updates Test
"""

import asyncio
import websockets
import json
from datetime import datetime
import sys

WS_URL = "ws://localhost:8000/api/ws/votes"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

async def test_websocket(complaint_id, duration=30):
    """Test WebSocket connection and receive updates"""
    
    uri = f"{WS_URL}/{complaint_id}"
    
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🔌 WEBSOCKET REAL-TIME TEST{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Connecting to: {uri}")
    
    try:
        async with websockets.connect(
            uri,
            ping_interval=20,  # Send ping every 20 seconds
            ping_timeout=10,   # Wait 10 seconds for pong
            close_timeout=10   # Timeout for close handshake
        ) as websocket:
            print(f"{GREEN}✅ Connected to WebSocket{RESET}\n")
            
            # Receive welcome message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📥 {YELLOW}Welcome Message:{RESET}")
                print(f"   Type: {data.get('type')}")
                print(f"   Message: {data.get('message')}")
                print(f"   Complaint ID: {data.get('complaint_id')}")
                print(f"   Timestamp: {data.get('timestamp')}\n")
            except asyncio.TimeoutError:
                print(f"{RED}⚠️  No welcome message received{RESET}\n")
            
            # Send ping test
            print(f"📤 Sending ping...")
            await websocket.send("ping")
            
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📥 {GREEN}Pong received:{RESET} {data.get('type')}\n")
            except asyncio.TimeoutError:
                print(f"{RED}⚠️  No pong received{RESET}\n")
            
            # Listen for vote updates
            print(f"{YELLOW}{'='*60}{RESET}")
            print(f"{YELLOW}⏳ Listening for vote updates ({duration} seconds)...{RESET}")
            print(f"{YELLOW}{'='*60}{RESET}")
            print(f"\n{BLUE}How to test:{RESET}")
            print(f"1. Open: http://localhost:8000/docs")
            print(f"2. Go to: POST /api/vote")
            print(f"3. Vote with this data:\n")
            print(f'{GREEN}{{')
            print(f'  "complaint_id": "{complaint_id}",')
            print(f'  "roll_number": "22CS{datetime.now().second:03d}",')
            print(f'  "vote_type": "upvote"')
            print(f'}}{RESET}\n')
            print(f"{YELLOW}Waiting for updates...{RESET}\n")
            
            vote_count = 0
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    # Calculate remaining time
                    elapsed = asyncio.get_event_loop().time() - start_time
                    remaining = duration - elapsed
                    
                    if remaining <= 0:
                        print(f"\n{YELLOW}⏱️  Time's up!{RESET}")
                        break
                    
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=min(1.0, remaining)
                    )
                    
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    if msg_type == 'vote_update':
                        vote_count += 1
                        print(f"\n{GREEN}{'='*60}{RESET}")
                        print(f"{GREEN}🗳️  VOTE UPDATE #{vote_count} RECEIVED!{RESET}")
                        print(f"{GREEN}{'='*60}{RESET}")
                        print(f"   Action: {YELLOW}{data.get('action')}{RESET}")
                        print(f"   Vote Type: {data.get('vote_type')}")
                        print(f"   Upvotes: {GREEN}{data.get('upvotes')}{RESET}")
                        print(f"   Downvotes: {RED}{data.get('downvotes')}{RESET}")
                        print(f"   Total Votes: {data.get('total_votes')}")
                        print(f"   Timestamp: {data.get('timestamp')}")
                        print(f"{GREEN}{'='*60}{RESET}\n")
                        print(f"{YELLOW}Still listening... ({int(remaining)}s remaining){RESET}\n")
                    
                    elif msg_type == 'status_update':
                        print(f"\n{BLUE}📊 Status Update:{RESET}")
                        print(f"   Old: {data.get('old_status')} → New: {data.get('new_status')}")
                    
                    elif msg_type == 'pong':
                        # Auto ping-pong, don't print
                        pass
                    
                    else:
                        print(f"\n{BLUE}📥 Message ({msg_type}):{RESET}")
                        print(f"   {json.dumps(data, indent=2)}")
                
                except asyncio.TimeoutError:
                    # Show countdown every second
                    elapsed = asyncio.get_event_loop().time() - start_time
                    remaining = int(duration - elapsed)
                    if remaining > 0 and remaining % 5 == 0:
                        print(f"{YELLOW}   ... {remaining}s remaining{RESET}")
                    continue
                
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"\n{RED}❌ Connection closed: {e}{RESET}")
                    break
            
            # Summary
            print(f"\n{BLUE}{'='*60}{RESET}")
            print(f"{BLUE}📊 TEST SUMMARY{RESET}")
            print(f"{BLUE}{'='*60}{RESET}")
            print(f"   Total vote updates received: {GREEN}{vote_count}{RESET}")
            print(f"   Duration: {duration}s")
            
            if vote_count > 0:
                print(f"\n{GREEN}✅ WebSocket is working perfectly!{RESET}")
                print(f"   Real-time updates are being broadcast successfully.")
            else:
                print(f"\n{YELLOW}⚠️  No vote updates received{RESET}")
                print(f"   This is normal if nobody voted during the test.")
                print(f"   Try voting while the test is running to see real-time updates.")
            
            print(f"{BLUE}{'='*60}{RESET}\n")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"{RED}❌ Connection failed: {e}{RESET}")
        print(f"{YELLOW}Make sure the backend is running on http://localhost:8000{RESET}")
    
    except ConnectionRefusedError:
        print(f"{RED}❌ Connection refused{RESET}")
        print(f"{YELLOW}Is the backend running? Start it with: python main.py{RESET}")
    
    except Exception as e:
        print(f"{RED}❌ WebSocket error: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def interactive_test():
    """Interactive test with user input"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🔌 CAMPUSVOICE WEBSOCKET TESTER{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Get complaint ID
    complaint_id = input(f"{YELLOW}Enter complaint ID (or press Enter to skip): {RESET}").strip()
    
    if not complaint_id:
        print(f"{RED}No complaint ID provided. Exiting.{RESET}")
        return
    
    # Get duration
    try:
        duration_input = input(f"{YELLOW}Test duration in seconds (default: 30): {RESET}").strip()
        duration = int(duration_input) if duration_input else 30
    except ValueError:
        duration = 30
        print(f"{YELLOW}Invalid input. Using default: 30 seconds{RESET}")
    
    print()
    await test_websocket(complaint_id, duration)


if __name__ == "__main__":
    try:
        asyncio.run(interactive_test())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(0)

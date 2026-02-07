#!/usr/bin/env python3
"""
Outbound Call Manager

Utility to initiate outbound calls via Twilio REST API.

Usage:
    python twilio/outbound_call.py --to +1234567890 --webhook https://your-domain.com/voice

Or programmatically:
    from twilio.outbound_call import OutboundCallManager

    manager = OutboundCallManager()
    call_sid = manager.make_call(
        to_number='+1234567890',
        webhook_url='https://your-domain.com/voice'
    )
"""

import os
import sys
from dotenv import load_dotenv
from twilio.rest import Client
from typing import Optional

load_dotenv()


class OutboundCallManager:
    """Manages outbound calls via Twilio"""

    def __init__(
        self,
        account_sid: str = None,
        auth_token: str = None,
        from_number: str = None
    ):
        """
        Initialize outbound call manager

        Args:
            account_sid: Twilio account SID (defaults to env var)
            auth_token: Twilio auth token (defaults to env var)
            from_number: Default Twilio phone number (defaults to env var)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_PHONE_NUMBER')

        if not self.account_sid:
            raise ValueError("TWILIO_ACCOUNT_SID not found")
        if not self.auth_token:
            raise ValueError("TWILIO_AUTH_TOKEN not found")
        if not self.from_number:
            raise ValueError("TWILIO_PHONE_NUMBER not found")

        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        print(f"✓ Twilio client initialized")
        print(f"  From: {self.from_number}")

    def make_call(
        self,
        to_number: str,
        webhook_url: str,
        from_number: str = None,
        status_callback: str = None,
        timeout: int = 60
    ) -> str:
        """
        Initiate an outbound call

        Args:
            to_number: Phone number to call (E.164 format, e.g., +1234567890)
            webhook_url: URL for TwiML configuration
            from_number: Twilio number to call from (optional, uses default)
            status_callback: URL for status callbacks (optional)
            timeout: Seconds to ring before giving up (default: 60)

        Returns:
            str: Call SID

        Raises:
            Exception: If call fails
        """
        if from_number is None:
            from_number = self.from_number

        print(f"\n📞 Initiating call...")
        print(f"   From: {from_number}")
        print(f"   To: {to_number}")
        print(f"   Webhook: {webhook_url}")

        try:
            call = self.client.calls.create(
                url=webhook_url,
                to=to_number,
                from_=from_number,
                status_callback=status_callback,
                timeout=timeout
            )

            print(f"✓ Call initiated")
            print(f"  Call SID: {call.sid}")
            print(f"  Status: {call.status}")

            return call.sid

        except Exception as e:
            print(f"❌ Call failed: {e}")
            raise

    def get_call_status(self, call_sid: str) -> dict:
        """
        Get status of a call

        Args:
            call_sid: Call SID

        Returns:
            dict: Call information
        """
        call = self.client.calls(call_sid).fetch()

        return {
            'sid': call.sid,
            'status': call.status,
            'direction': call.direction,
            'from': call.from_,
            'to': call.to,
            'duration': call.duration,
            'start_time': call.start_time,
            'end_time': call.end_time,
        }

    def hangup_call(self, call_sid: str):
        """
        Hang up an active call

        Args:
            call_sid: Call SID
        """
        print(f"\n📴 Hanging up call: {call_sid}")

        call = self.client.calls(call_sid).update(status='completed')

        print(f"✓ Call ended: {call.status}")

    def list_active_calls(self) -> list:
        """
        List all active calls

        Returns:
            list: List of active call SIDs
        """
        calls = self.client.calls.list(status='in-progress')

        return [call.sid for call in calls]


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Initiate outbound call via Twilio"
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Call command
    call_parser = subparsers.add_parser('call', help='Make outbound call')
    call_parser.add_argument(
        '--to',
        required=True,
        help='Phone number to call (E.164 format, e.g., +1234567890)'
    )
    call_parser.add_argument(
        '--webhook',
        required=True,
        help='TwiML webhook URL (e.g., https://your-domain.com/voice)'
    )
    call_parser.add_argument(
        '--from',
        dest='from_number',
        help='Twilio number to call from (default: TWILIO_PHONE_NUMBER env var)'
    )
    call_parser.add_argument(
        '--status-callback',
        help='URL for status callbacks (optional)'
    )
    call_parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Ring timeout in seconds (default: 60)'
    )

    # Status command
    status_parser = subparsers.add_parser('status', help='Get call status')
    status_parser.add_argument('call_sid', help='Call SID')

    # Hangup command
    hangup_parser = subparsers.add_parser('hangup', help='Hang up call')
    hangup_parser.add_argument('call_sid', help='Call SID')

    # List command
    list_parser = subparsers.add_parser('list', help='List active calls')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        manager = OutboundCallManager()

        if args.command == 'call':
            # Make call
            call_sid = manager.make_call(
                to_number=args.to,
                webhook_url=args.webhook,
                from_number=getattr(args, 'from_number', None),
                status_callback=args.status_callback,
                timeout=args.timeout
            )

            print(f"\n✓ Call in progress")
            print(f"  Track status: python {sys.argv[0]} status {call_sid}")
            print(f"  Hang up: python {sys.argv[0]} hangup {call_sid}")

        elif args.command == 'status':
            # Get call status
            status = manager.get_call_status(args.call_sid)
            print(f"\n📊 Call Status:")
            for key, value in status.items():
                print(f"   {key}: {value}")

        elif args.command == 'hangup':
            # Hang up call
            manager.hangup_call(args.call_sid)

        elif args.command == 'list':
            # List active calls
            calls = manager.list_active_calls()
            print(f"\n📋 Active Calls: {len(calls)}")
            for call_sid in calls:
                print(f"   - {call_sid}")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

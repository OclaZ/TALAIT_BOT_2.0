import json
import os
from datetime import datetime
from utils.constants import DATA_DIR, LEADERBOARD_FILE, HALL_OF_FAME_FILE, CHALLENGES_FILE

class DataManager:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.leaderboard_file = LEADERBOARD_FILE
        self.hall_of_fame_file = HALL_OF_FAME_FILE
        self.challenges_file = CHALLENGES_FILE
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.leaderboard = self._load_data(self.leaderboard_file)
        self.hall_of_fame = self._load_data(self.hall_of_fame_file)
        self.challenges = self._load_data(self.challenges_file)
        
        # Fix for challenges file - should be a list not dict
        if isinstance(self.challenges, dict):
            self.challenges = []
        
        # Initialize tickets list in leaderboard if not exists
        if 'tickets' not in self.leaderboard:
            self.leaderboard['tickets'] = []

    def _load_data(self, filename):
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {} if filename != self.challenges_file else []

    def _save_data(self, filename, data):
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def get_month_key(self):
        now = datetime.now()
        return f"{now.year}-{now.month:02d}"

    def ensure_user(self, user_id, username):
        user_id = str(user_id)
        if user_id not in self.leaderboard:
            self.leaderboard[user_id] = {
                'username': username,
                'xp': 0,
                'weekly_xp': {},
                'total_xp': 0,
                'badges': []
            }
        else:
            self.leaderboard[user_id]['username'] = username
        self._save_data(self.leaderboard_file, self.leaderboard)

    def add_xp(self, user_id, amount, week_key):
        user_id = str(user_id)
        self.leaderboard[user_id]['xp'] += amount
        self.leaderboard[user_id]['total_xp'] += amount
        
        if week_key not in self.leaderboard[user_id]['weekly_xp']:
            self.leaderboard[user_id]['weekly_xp'][week_key] = 0
        self.leaderboard[user_id]['weekly_xp'][week_key] += amount
        
        self._save_data(self.leaderboard_file, self.leaderboard)

    def remove_xp(self, user_id, amount):
        user_id = str(user_id)
        self.leaderboard[user_id]['xp'] = max(0, self.leaderboard[user_id]['xp'] - amount)
        self._save_data(self.leaderboard_file, self.leaderboard)

    def add_badge(self, user_id, badge):
        user_id = str(user_id)
        if 'badges' not in self.leaderboard[user_id]:
            self.leaderboard[user_id]['badges'] = []
        if badge not in self.leaderboard[user_id]['badges']:
            self.leaderboard[user_id]['badges'].append(badge)
        self._save_data(self.leaderboard_file, self.leaderboard)

    def get_user(self, user_id):
        return self.leaderboard.get(str(user_id))

    def get_leaderboard(self):
        # Return only user data, not tickets
        return {k: v for k, v in self.leaderboard.items() if k != 'tickets'}

    def get_hall_of_fame(self):
        return self.hall_of_fame

    def get_user_rank(self, user_id):
        leaderboard_data = self.get_leaderboard()
        sorted_users = sorted(leaderboard_data.items(), key=lambda x: x[1]['xp'], reverse=True)
        rank = next((i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == str(user_id)), 0)
        return rank

    def reset_monthly_leaderboard(self):
        month_key = self.get_month_key()
        
        # Get only user data for hall of fame
        leaderboard_data = self.get_leaderboard()
        self.hall_of_fame[month_key] = dict(leaderboard_data)
        self._save_data(self.hall_of_fame_file, self.hall_of_fame)
        
        # Reset monthly XP but keep total XP and tickets
        for user_id in leaderboard_data:
            self.leaderboard[user_id]['xp'] = 0
        
        self._save_data(self.leaderboard_file, self.leaderboard)

    # Challenge management
    def create_challenge(self, challenge_data):
        """Create a new challenge"""
        challenge_id = len(self.challenges) + 1
        challenge_data['id'] = challenge_id
        self.challenges.append(challenge_data)
        self._save_data(self.challenges_file, self.challenges)
        return challenge_id

    def update_challenge(self, challenge_id, updates):
        """Update an existing challenge"""
        for challenge in self.challenges:
            if challenge['id'] == challenge_id:
                challenge.update(updates)
                self._save_data(self.challenges_file, self.challenges)
                return True
        return False

    def get_active_challenge(self):
        """Get the current active challenge"""
        for challenge in reversed(self.challenges):
            if challenge.get('status') == 'active':
                return challenge
        return None

    def get_latest_challenge(self):
        """Get the most recent challenge"""
        return self.challenges[-1] if self.challenges else None

    def add_submission(self, challenge_id, submission_data):
        """Add a submission to a challenge"""
        for challenge in self.challenges:
            if challenge['id'] == challenge_id:
                if 'submissions' not in challenge:
                    challenge['submissions'] = []
                challenge['submissions'].append(submission_data)
                self._save_data(self.challenges_file, self.challenges)
                return True
        return False

    # Ticket management
    def create_ticket(self, ticket_data):
        """Create a new ticket"""
        if 'tickets' not in self.leaderboard:
            self.leaderboard['tickets'] = []
        
        ticket_id = len(self.leaderboard['tickets']) + 1
        ticket_data['id'] = ticket_id
        self.leaderboard['tickets'].append(ticket_data)
        self._save_data(self.leaderboard_file, self.leaderboard)
        return ticket_id

    def update_ticket(self, ticket_id, updates):
        """Update an existing ticket"""
        if 'tickets' not in self.leaderboard:
            return False
        
        for ticket in self.leaderboard['tickets']:
            if ticket['id'] == ticket_id:
                ticket.update(updates)
                self._save_data(self.leaderboard_file, self.leaderboard)
                return True
        return False

    def get_user_ticket(self, user_id, challenge_id):
        """Get a user's ticket for a specific challenge"""
        if 'tickets' not in self.leaderboard:
            return None
        
        for ticket in self.leaderboard['tickets']:
            if (ticket['user_id'] == user_id and 
                ticket['challenge_id'] == challenge_id and 
                ticket['status'] == 'open'):
                return ticket
        return None

    def get_ticket_by_channel(self, channel_id):
        """Get ticket by channel ID"""
        if 'tickets' not in self.leaderboard:
            return None
        
        for ticket in self.leaderboard['tickets']:
            if ticket['channel_id'] == channel_id:
                return ticket
        return None

    def get_tickets_by_challenge(self, challenge_id):
        """Get all tickets for a specific challenge"""
        if 'tickets' not in self.leaderboard:
            return []
        
        return [t for t in self.leaderboard['tickets'] if t['challenge_id'] == challenge_id]
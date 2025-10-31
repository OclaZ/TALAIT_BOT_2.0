import json
import os
from datetime import datetime
from utils.constants import DATA_DIR, LEADERBOARD_FILE, HALL_OF_FAME_FILE, CHALLENGES_FILE
from utils.logger import get_logger

logger = get_logger("data_manager")

class DataManager:
    def __init__(self):
        self.data_dir = DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        self.server_data = {}
        logger.info(f"DataManager initialized | Data directory: {self.data_dir}")
    
    def _get_server_dir(self, guild_id: int) -> str:
        server_dir = os.path.join(self.data_dir, f'server_{guild_id}')
        if not os.path.exists(server_dir):
            os.makedirs(server_dir, exist_ok=True)
            logger.debug(f"Created server directory | Guild: {guild_id}")
        return server_dir
    
    def _load_server_data(self, guild_id: int, filename: str):
        server_dir = self._get_server_dir(guild_id)
        filepath = os.path.join(server_dir, filename)

        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded {filename} | Guild: {guild_id}")
                    return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filename} | Guild: {guild_id} | Error: {e}")
        except Exception as e:
            logger.error(f"Error loading {filename} | Guild: {guild_id} | Error: {e}")

        logger.debug(f"File not found or error, returning empty data | {filename} | Guild: {guild_id}")
        if filename == CHALLENGES_FILE:
            return []
        return {}
    
    def _save_server_data(self, guild_id: int, filename: str, data):
        server_dir = self._get_server_dir(guild_id)
        filepath = os.path.join(server_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            logger.debug(f"Saved {filename} | Guild: {guild_id}")
        except Exception as e:
            logger.error(f"Error saving {filename} | Guild: {guild_id} | Error: {e}")
    
    def get_month_key(self):
        now = datetime.now()
        return f"{now.year}-{now.month:02d}"
    
    def ensure_user(self, guild_id: int, user_id: int, username: str):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        user_id = str(user_id)
        
        if user_id not in leaderboard:
            leaderboard[user_id] = {
                'username': username,
                'xp': 0,
                'weekly_xp': {},
                'total_xp': 0,
                'badges': []
            }
        else:
            leaderboard[user_id]['username'] = username
        
        self._save_server_data(guild_id, LEADERBOARD_FILE, leaderboard)
    
    def add_xp(self, guild_id: int, user_id: int, amount: int, week_key: str):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        user_id = str(user_id)

        leaderboard[user_id]['xp'] += amount
        leaderboard[user_id]['total_xp'] += amount

        if week_key not in leaderboard[user_id]['weekly_xp']:
            leaderboard[user_id]['weekly_xp'][week_key] = 0
        leaderboard[user_id]['weekly_xp'][week_key] += amount

        self._save_server_data(guild_id, LEADERBOARD_FILE, leaderboard)
        logger.info(f"Added {amount} XP | User: {leaderboard[user_id]['username']} | Total: {leaderboard[user_id]['xp']} | Guild: {guild_id}")
    
    def remove_xp(self, guild_id: int, user_id: int, amount: int):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        user_id = str(user_id)
        
        if user_id in leaderboard:
            leaderboard[user_id]['xp'] = max(0, leaderboard[user_id]['xp'] - amount)
            self._save_server_data(guild_id, LEADERBOARD_FILE, leaderboard)
    
    def add_badge(self, guild_id: int, user_id: int, badge: str):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        user_id = str(user_id)
        
        if user_id in leaderboard:
            if 'badges' not in leaderboard[user_id]:
                leaderboard[user_id]['badges'] = []
            if badge not in leaderboard[user_id]['badges']:
                leaderboard[user_id]['badges'].append(badge)
            self._save_server_data(guild_id, LEADERBOARD_FILE, leaderboard)
    
    def get_user(self, guild_id: int, user_id: int):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        return leaderboard.get(str(user_id))
    
    def get_leaderboard(self, guild_id: int):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        return {k: v for k, v in leaderboard.items() if k != 'tickets'}
    
    def get_user_rank(self, guild_id: int, user_id: int):
        leaderboard_data = self.get_leaderboard(guild_id)
        sorted_users = sorted(leaderboard_data.items(), key=lambda x: x[1]['xp'], reverse=True)
        rank = next((i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == str(user_id)), 0)
        return rank
    
    def get_user_streak(self, guild_id: int, user_id: int):
        user = self.get_user(guild_id, user_id)
        if not user:
            return 0
        return len(user.get('weekly_xp', {}))
    
    def get_hall_of_fame(self, guild_id: int):
        return self._load_server_data(guild_id, HALL_OF_FAME_FILE)
    
    def reset_monthly_leaderboard(self, guild_id: int):
        month_key = self.get_month_key()
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        hall_of_fame = self._load_server_data(guild_id, HALL_OF_FAME_FILE)

        leaderboard_data = {k: v for k, v in leaderboard.items() if k != 'tickets'}
        user_count = len(leaderboard_data)
        hall_of_fame[month_key] = dict(leaderboard_data)
        self._save_server_data(guild_id, HALL_OF_FAME_FILE, hall_of_fame)

        for user_id in leaderboard_data:
            leaderboard[user_id]['xp'] = 0

        self._save_server_data(guild_id, LEADERBOARD_FILE, leaderboard)
        logger.info(f"Monthly leaderboard reset | Month: {month_key} | Users: {user_count} | Guild: {guild_id}")
    
    def create_challenge(self, guild_id: int, challenge_data: dict):
        challenges = self._load_server_data(guild_id, CHALLENGES_FILE)
        challenge_id = len(challenges) + 1
        challenge_data['id'] = challenge_id
        challenge_data['guild_id'] = guild_id
        challenges.append(challenge_data)
        self._save_server_data(guild_id, CHALLENGES_FILE, challenges)
        logger.info(f"Challenge created | ID: {challenge_id} | Difficulty: {challenge_data.get('difficulty', 'N/A')} | Guild: {guild_id}")
        return challenge_id
    
    def update_challenge(self, guild_id: int, challenge_id: int, updates: dict):
        challenges = self._load_server_data(guild_id, CHALLENGES_FILE)
        for challenge in challenges:
            if challenge['id'] == challenge_id:
                challenge.update(updates)
                self._save_server_data(guild_id, CHALLENGES_FILE, challenges)
                return True
        return False
    
    def get_active_challenge(self, guild_id: int):
        challenges = self._load_server_data(guild_id, CHALLENGES_FILE)
        for challenge in reversed(challenges):
            if challenge.get('status') == 'active':
                return challenge
        return None
    
    def get_latest_challenge(self, guild_id: int):
        challenges = self._load_server_data(guild_id, CHALLENGES_FILE)
        return challenges[-1] if challenges else None
    
    def get_challenge_by_id(self, guild_id: int, challenge_id: int):
        challenges = self._load_server_data(guild_id, CHALLENGES_FILE)
        for challenge in challenges:
            if challenge['id'] == challenge_id:
                return challenge
        return None
    
    def add_submission(self, guild_id: int, challenge_id: int, submission_data: dict):
        challenges = self._load_server_data(guild_id, CHALLENGES_FILE)
        for challenge in challenges:
            if challenge['id'] == challenge_id:
                if 'submissions' not in challenge:
                    challenge['submissions'] = []
                challenge['submissions'].append(submission_data)
                self._save_server_data(guild_id, CHALLENGES_FILE, challenges)
                return True
        return False
    
    def create_ticket(self, guild_id: int, ticket_data: dict):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        if 'tickets' not in leaderboard:
            leaderboard['tickets'] = []
        ticket_id = len(leaderboard['tickets']) + 1
        ticket_data['id'] = ticket_id
        ticket_data['guild_id'] = guild_id
        leaderboard['tickets'].append(ticket_data)
        self._save_server_data(guild_id, LEADERBOARD_FILE, leaderboard)
        return ticket_id
    
    def update_ticket(self, guild_id: int, ticket_id: int, updates: dict):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        if 'tickets' not in leaderboard:
            return False
        for ticket in leaderboard['tickets']:
            if ticket['id'] == ticket_id:
                ticket.update(updates)
                self._save_server_data(guild_id, LEADERBOARD_FILE, leaderboard)
                return True
        return False
    
    def get_user_ticket(self, guild_id: int, user_id: int, challenge_id: int):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        if 'tickets' not in leaderboard:
            return None
        for ticket in leaderboard['tickets']:
            if (ticket['user_id'] == user_id and 
                ticket['challenge_id'] == challenge_id and 
                ticket['status'] == 'open'):
                return ticket
        return None
    
    def get_ticket_by_channel(self, guild_id: int, channel_id: int):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        if 'tickets' not in leaderboard:
            return None
        for ticket in leaderboard['tickets']:
            if ticket['channel_id'] == channel_id:
                return ticket
        return None
    
    def get_tickets_by_challenge(self, guild_id: int, challenge_id: int):
        leaderboard = self._load_server_data(guild_id, LEADERBOARD_FILE)
        if 'tickets' not in leaderboard:
            return []
        return [t for t in leaderboard['tickets'] if t['challenge_id'] == challenge_id]
def __init__(self):
    self.data_dir = DATA_DIR
    self.leaderboard_file = LEADERBOARD_FILE
    self.hall_of_fame_file = HALL_OF_FAME_FILE
    self.challenges_file = CHALLENGES_FILE  # Add this
    
    os.makedirs(self.data_dir, exist_ok=True)
    
    self.leaderboard = self._load_data(self.leaderboard_file)
    self.hall_of_fame = self._load_data(self.hall_of_fame_file)
    self.challenges = self._load_data(self.challenges_file)  # Add this
    
    # Fix for challenges file - should be a list not dict
    if isinstance(self.challenges, dict):
        self.challenges = []
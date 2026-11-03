'''
    Class for defining a vote. Each vote has a list of involved messages, a dictionary relating message id to number of
    votes, a dictionary of voter ids and whether they have voted/vetoed, and a list of winners/vetoed selections that
    are initially set to None.
'''
class Vote :
    # Variables that represent a vote
    messages = []
    votes : {str: int} = {}
    voters : {str: [str, str]} = {}
    winners = None
    vetoes = None

    def __init__(self, messages, total_votes):
        self.messages = messages
        self.total_votes = total_votes
        self.votes = {}
        self.voters = {}
        for message in self.messages :
            self.votes[message] = 0

    # Add a vote
    def add_vote(self, message_id : str, voter: str):

        # If they aren't in the users who have voted, add them with a single vote. also add a vote for message
        if voter not in self.voters:
            self.voters[voter] = ["vote"]
            self.votes[message_id] += 1

        # If they are present but haven't voted, add them with a single vote. also add a vote for message
        elif not ("vote" in self.voters[voter]):
            self.voters[voter].append("vote")
            self.votes[message_id] += 1

    def remove_vote(self, message_id : str, voter: str):

        self.voters[voter].remove("vote")
        self.votes[message_id] -= 1

    def remove_veto(self, message_id : str, voter: str):

        self.voters[voter].remove("veto")
        self.votes[message_id] += 10

    # Add a veto
    def veto(self, message_id : str, voter : str):

        # If they aren't in the users who have voted, add them with a single veto. also add a veto to message
        if voter not in self.voters:
            self.voters[voter] = ["veto"]
            self.votes[message_id] = -10


        # If they are present but haven't vetoed, add them with a single veto. also add a veto to message
        elif not ("veto" in self.voters[voter]):
            self.voters[voter].append("veto")
            self.votes[message_id] = -10

    # End a vote that is in progress
    def end_vote(self):

        # If this vote has already been ended, return previous result
        if self.winners is not None: return self.winners, self.vetoes

        # Keep track of top results and vetoed results
        winners = [["default", -1]]
        vetoes = []

        # Check each messages vote counts and compare
        for message in self.messages:
            x = [message, self.votes[message]]

            # If greater, replace winners
            if x[1] > winners[0][1]:
                winners = [x]

            # If equal, append to winners
            elif x[1] == winners[0][1]:
                winners.append(x)

            # If less than 0, it's been vetoed
            elif x[1] < 0:
                vetoes.append([message, -10])

        # return winner and veto lists
        self.winners = winners
        self.vetoes = vetoes
        return winners, vetoes

    # Function that checks if the vote has enough voter participation to end
    def check_vote(self):

        # Check if all votes are cast
        cast_votes = 0
        voter_list = self.voters.keys()

        # Go through all voters to see how many have voted
        for voter in voter_list:
            if ("vote" in self.voters[voter]) and ("veto" in self.voters[voter]):
                cast_votes += 1

            elif ("vote" in self.voters[voter]) and len(voter_list) > self.total_votes-1 :
                cast_votes += 1

        # If enough people (all) have voted, end vote. Otherwise don't
        if cast_votes >= self.total_votes:
            result = self.end_vote()

        else:
            result = None, None

        return result
import discord
import vote

from discord.ext import commands

'''
    beanBot cog for polling. Mostly handles dinner voting.
'''
class Poll(commands.Cog) :
    num_voters = 0
    active_vote = None
    vote_reacts = ["✅","this","thumbsup"]
    veto_reacts = ["❎","thumbsdown"]

    def __init__(self, bot):
        self.bot = bot

    # Command Handler for starting a vote
    @commands.slash_command(name="poll", description="Start a vote based on given input.")
    async def poll(self, ctx: discord.ApplicationContext, text_input: discord.SlashCommandOptionType.string):

        # Check the number of people voting (will probably always be 3 lol) subtract one for bean bot
        self.num_voters = ctx.guild.member_count - 1
        if self.num_voters < 3: self.num_voters = 3

        await ctx.respond("Here are today's meal planning options. You may veto one selection, please vote only once and veto once.")

        # For all options, post a message for voting on! Keep track of all messages in this voting block
        options = self.parse_input(text_input.strip())
        messages = []
        for option in options:
            message = await ctx.send(option.strip())
            messages.append(message.id)


        vote_obj = vote.Vote(messages, self.num_voters)
        self.active_vote = vote_obj

    # Reaction handler for processing votes and vetoes
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # If there is no active vote, the source message is not involved in the active vote, or the last vote has closed, ignore react
        if (self.active_vote is None) or (payload.message_id not in self.active_vote.messages) or (self.active_vote.winners is not None):
            return None

        # Determine if this is a veto or a vote react. Add correct one to member
        if payload.emoji.name in self.vote_reacts:
            self.active_vote.add_vote(payload.message_id, str(payload.member.id))

        elif payload.emoji.name in self.veto_reacts:
            self.active_vote.veto(payload.message_id, str(payload.member.id))

        # Check the current vote to see if this vote/veto has brought us to enough to end the vote
        final_message = ""
        winners, vetos = self.active_vote.check_vote()

        # Get the channel of vote message
        channel : discord.ChannelType = await self.bot.fetch_channel(payload.channel_id)

        # If winners exist, the vote has ended!
        if winners is not None :
            win_text = ""

            # If ties, stitch together a message
            if len(winners) > 1 :
                final_message = "The following meals tied: "
                for winner in winners:
                    win_m = await channel.fetch_message(int(winner[0]))
                    win_text = win_m.content
                    final_message = final_message + win_text + ", "

                final_message = final_message[:-2]
                final_message = final_message + ". "

            # If only one winner, grab it and write announcement message
            else:
                win_m = await channel.fetch_message(int(winners[0][0]))
                win_text = win_m.content
                final_message = "The winning selection was: " + win_text + ". "

            # If anything has been vetoed, announce that
            if len(vetos) > 0:
                final_message = final_message + "The following was vetoed: "
                for veto in vetos:
                    veto_m = await channel.fetch_message(int(veto[0]))
                    veto_text = veto_m.content
                    final_message = final_message + veto_text + ", "

                final_message = final_message[:-2]
                final_message = final_message + "."

            # Reset the active vote and send the final message
            self.active_vote = None
            return await channel.send(final_message)
        return None

    # Reaction handler for processing votes and vetoes
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        # If there is no active vote, the source message is not involved in the active vote, or the last vote has closed, ignore react
        if (self.active_vote is None) or (payload.message_id not in self.active_vote.messages) or (self.active_vote.winners is not None):
            return None

        # Determine if this is a veto or a vote react. Add correct one to member
        if payload.emoji.name in self.vote_reacts:
            self.active_vote.remove_vote(payload.message_id, str(payload.user_id))

        elif payload.emoji.name in self.veto_reacts:
            self.active_vote.remove_veto(payload.message_id, str(payload.user_id))

        return None

    def parse_input(self, text):

        # Check if copy/pasted from notepad
        notepad = False
        options = []
        if text.startswith("-") or text.startswith(" -"):
            notepad = True

        if notepad:
            x = text.index("]")
            split_text = text[:x+1]
            options = text.split(split_text)
            for option in options:
                print(option)

            options = options[1:]

        else:
            options = text.split(",")


        return options

# I don't know what this does, but I know i need it! something about initializing the cog
def setup(bot):
    bot.add_cog(Poll(bot))
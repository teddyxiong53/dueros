import logging
from sdk.dueros_core import DuerOS
from app.framework.mic import Audio
from app.framework.player import Player
from app.utils.prompt_tone import PromptTone

logging.basicConfig(level=logging.INFO)


def directive_listener(directive_content):
	content = u"the content from baidu server is :%s " % (directive_content)
	logging.info(content)
	
	
def main():
	audio = Audio()
	player = Player()
	dueros = DuerOS(player)
	dueros.set_directive_listener(directive_listener)
	
	audio.link(dueros)
	dueros.start()
	audio.start()
	
	prompt_tone_player = PromptTone()
	
	while True:
		try:
			try:
				print '\n'
				input('input [ENTER] key to start conversation\n')
			except SyntaxError:
				pass
			prompt_tone_player.play()
			dueros.listen()
			
		except KeyboardInterrupt:
			break
			
	dueros.stop()
	audio.stop()
	
if __name__ == '__main__':
	main()

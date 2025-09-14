import asyncio
from models.openai_model_client import get_model_client
from teams.analyzer_gpt import getDataAnalyzerTeam
from config.docker_utils import getDockerCommandLineExecutor,start_docker_container,stop_docker_container
from autogen_agentchat.messages import TextMessage

async def main():

    openai_model_client = get_model_client()
    docker = getDockerCommandLineExecutor()

    team = getDataAnalyzerTeam(docker,openai_model_client)

    try:
        task = 'Can you give me the graph of  no.of people died and survived from the data of titanic.csv and save it as output.png '

        await start_docker_container(docker)

        async for message in team.run_stream(task=task):
            print(message)

    except Exception as e:
        print(e)
    finally:
        await stop_docker_container(docker)


if(__name__=='__main__'):
    asyncio.run(main())
if __name__ == '__main__':
  import dotenv
  import argparse
  import importlib
  
  dotenv.load_dotenv()
  parser = argparse.ArgumentParser(description='Matching Service')
  parser.add_argument('--start', nargs='+', default=['syncopate'], help='Start Service')
  args = parser.parse_args()
  for name in args.start:
    MatcherModule = importlib.import_module(f'matching_service.{name}')
    MatcherModule.start()

  from matching_service.api import app
  import uvicorn
  uvicorn.run(app, host="0.0.0.0")
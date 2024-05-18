import click

@click.group()
def cli():
    pass

@cli.command()
def runserver():
    """Run the Flask server."""
    from subprocess import run
    run(['python3 server.py'], cwd='../back-end', shell=True)

@cli.command()
def build():
    """Build the React frontend."""
    from subprocess import run
    run(['npm start'], cwd='../front-end', shell=True)

if __name__ == '__main__':
    cli()


    

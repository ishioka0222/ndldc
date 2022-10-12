import click


@click.group()
def cli():
    pass


@cli.command()
def download():
    print("hello world")


def main():
    cli()


if __name__ == '__main__':
    main()

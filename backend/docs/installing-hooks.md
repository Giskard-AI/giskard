# Installing pre-commit hooks

We use pre-commit hooks to apply Google's Java Format tool, which helps keep the code standard across all commiters.

To do this, we use a tool named `pre-commit`, which can be installed with:
> pip install pre-commit

Once installed, at the root of the giskard repo, you can run the command
> pre-commit install

which will setup pre-commit hook scripts.

Now, on your next commit changes done to the Java code will trigger a cleanup of the file.
If all Java files are correct, it'll push. If they contain something that is not within the format's specifications, the
changes will be automatically applied and you will need to stage the files and commit again.

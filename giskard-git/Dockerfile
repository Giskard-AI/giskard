FROM node:alpine

RUN apk add --no-cache tini git \
    && yarn global add git-http-server \
    && adduser -D -g git git

USER git
WORKDIR /home/git

RUN git init --bare repository.git

RUN cd repository.git && git symbolic-ref HEAD refs/heads/main
RUN git config --global user.email "giskard@example.com" && git config --global user.name "Giskard"

RUN git clone repository.git

WORKDIR repository

RUN echo "This is a Git repository where you can add an modify your Giskard test files" > README
RUN git add README && git commit -am "Init Repo" && git push

EXPOSE 3000

ENTRYPOINT ["tini", "--", "git-http-server", "-p", "3000", "/home/git"]
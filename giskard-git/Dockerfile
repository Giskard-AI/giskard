FROM node:alpine

RUN apk add --no-cache git \
    && yarn global add git-http-server \
    && adduser -D -g git git

USER git
WORKDIR /giskard-home/git

RUN git init --bare created_tests

ENTRYPOINT ["git-http-server", "-p", "1234", "/giskard-home/git"]
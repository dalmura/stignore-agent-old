FROM python:3.9-buster

WORKDIR /build

COPY bin /build/bin
COPY stignore_agent /build/stignore_agent
COPY setup.cfg pyproject.toml README.md LICENSE /build/

RUN pip3 install --upgrade setuptools wheel build
RUN python3 -m build


FROM python:3.9-buster

COPY --from=0 /build/dist/stignore_agent-*-py3-none-any.whl /tmp/
RUN pip3 install /tmp/stignore_agent-*-py3-none-any.whl && rm /tmp/stignore_agent-*-py3-none-any.whl

ENTRYPOINT ["/usr/local/bin/stignore-agent"]

##
## Copyright 2023 Ocean Protocol Foundation
## SPDX-License-Identifier: Apache-2.0
##
FROM ubuntu:18.04
LABEL maintainer="Ocean Protocol <devops@oceanprotocol.com>"

ARG VERSION

RUN apt-get update && \
   apt-get install --no-install-recommends -y \
   gcc \
   python3.8 \
   python3-pip \
   python3.8-dev \
   gettext-base

COPY . /ocean-provider
WORKDIR /ocean-provider

RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install setuptools
RUN python3.8 -m pip install wheel
RUN python3.8 -m pip install .

ENV NETWORK_URL='https://rpc.goerli.eth.gateway.fm'

ENV PROVIDER_PRIVATE_KEY='secrets.PROVIDER_PRIVATE_KEY'
ENV PROVIDER_ADDRESS=''

ENV AZURE_ACCOUNT_NAME=''
ENV AZURE_ACCOUNT_KEY=''
ENV AZURE_RESOURCE_GROUP=''
ENV AZURE_LOCATION=''
ENV AZURE_CLIENT_ID=''
ENV AZURE_CLIENT_SECRET=''
ENV AZURE_TENANT_ID=''
ENV AZURE_SUBSCRIPTION_ID=''

# do checksums only if file size < 5 Mb
ENV MAX_CHECKSUM_LENGTH='5242880'

# Note: AZURE_SHARE_INPUT and AZURE_SHARE_OUTPUT are only used
# for Azure Compute data assets (not for Azure Storage data assets).
# If you're not supporting Azure Compute, just leave their values
# as 'compute' and 'output', respectively.
ENV AZURE_SHARE_INPUT='compute'
ENV AZURE_SHARE_OUTPUT='output'

ENV OCEAN_PROVIDER_URL='http://0.0.0.0:8030'


ENV OCEAN_PROVIDER_WORKERS='1'
ENV OCEAN_PROVIDER_TIMEOUT='9000'
ENV ALLOW_NON_PUBLIC_IP=False
ENV ARWEAVE_GATEWAY=https://arweave.net/
ENV IPFS_GATEWAY=https://ipfs.io


ENTRYPOINT ["/ocean-provider/docker-entrypoint.sh"]

EXPOSE 8030

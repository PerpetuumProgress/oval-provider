#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_provider.constants import BaseURLs
from ocean_provider.utils.accounts import generate_auth_token, sign_message
from ocean_provider.utils.currency import to_wei
from ocean_provider.utils.services import ServiceType
from tests.test_helpers import (
    BLACK_HOLE_ADDRESS,
    get_dataset_asset_with_access_service,
    get_dataset_ddo_disabled,
    get_dataset_ddo_with_denied_consumer,
    get_dataset_ddo_with_multiple_files,
    get_dataset_with_invalid_url_ddo,
    get_dataset_with_ipfs_url_ddo,
    get_nonce,
    initialize_service,
    mint_100_datatokens,
    start_order,
)


@pytest.mark.parametrize("userdata", [False, "valid", "invalid"])
def test_download_service(client, publisher_wallet, consumer_wallet, web3, userdata):
    asset = get_dataset_asset_with_access_service(client, publisher_wallet)
    service = asset.get_service_by_type(ServiceType.ACCESS)
    mint_100_datatokens(
        web3, service.datatoken_address, consumer_wallet.address, publisher_wallet
    )
    tx_id, _ = start_order(
        web3,
        service.datatoken_address,
        consumer_wallet.address,
        to_wei(1),
        service.index,
        BLACK_HOLE_ADDRESS,
        BLACK_HOLE_ADDRESS,
        0,
        consumer_wallet,
    )

    # Consume using url index and auth token
    # (let the provider do the decryption)
    payload = {
        "documentId": asset.did,
        "serviceId": service.id,
        "serviceType": service.type,
        "dataToken": service.datatoken_address,
        "consumerAddress": consumer_wallet.address,
        "signature": generate_auth_token(consumer_wallet),
        "transferTxId": tx_id,
        "fileIndex": 0,
    }

    if userdata:
        payload["userdata"] = (
            '{"surname":"XXX", "age":12}' if userdata == "valid" else "cannotdecode"
        )

    download_endpoint = BaseURLs.SERVICES_URL + "/download"
    response = client.get(download_endpoint, query_string=payload)
    assert response.status_code == 200, f"{response.data}"

    # Consume using url index and signature (withOUT nonce), should fail
    payload["signature"] = sign_message(asset.did, consumer_wallet)
    print(">>>> Expecting InvalidSignatureError from the download endpoint <<<<")

    response = client.get(download_endpoint, query_string=payload)
    assert response.status_code == 400, f"{response.data}"

    # Consume using url index and signature (with nonce)
    nonce = get_nonce(client, consumer_wallet.address)
    _msg = f"{asset.did}{nonce}"
    payload["signature"] = sign_message(_msg, consumer_wallet)
    response = client.get(download_endpoint, query_string=payload)
    assert response.status_code == 200, f"{response.data}"


def test_empty_payload(client):
    consume = client.get(
        BaseURLs.SERVICES_URL + "/download", data=None, content_type="application/json"
    )
    assert consume.status_code == 400


def test_initialize_on_bad_url(client, publisher_wallet, consumer_wallet, web3):
    asset = get_dataset_with_invalid_url_ddo(client, publisher_wallet)
    service = asset.get_service_by_type(ServiceType.ACCESS)

    mint_100_datatokens(
        web3, service.datatoken_address, consumer_wallet.address, publisher_wallet
    )

    response = initialize_service(
        client,
        asset.did,
        service.id,
        service.type,
        service.datatoken_address,
        consumer_wallet,
        raw_response=True,
    )
    assert "error" in response.json
    assert response.json["error"] == "Asset URL not found or not available."


def test_initialize_on_ipfs_url(client, publisher_wallet, consumer_wallet, web3):
    asset = get_dataset_with_ipfs_url_ddo(client, publisher_wallet)
    service = asset.get_service_by_type(ServiceType.ACCESS)

    mint_100_datatokens(
        web3, service.datatoken_address, consumer_wallet.address, publisher_wallet
    )

    numTokens, datatoken, _, _ = initialize_service(
        client,
        asset.did,
        service.id,
        service.type,
        service.datatoken_address,
        consumer_wallet,
    )

    assert numTokens == 1
    assert datatoken == service.datatoken_address


def test_initialize_on_disabled_asset(client, publisher_wallet, consumer_wallet, web3):
    asset, real_asset = get_dataset_ddo_disabled(client, publisher_wallet)
    assert real_asset
    service = asset.get_service_by_type(ServiceType.ACCESS)

    mint_100_datatokens(
        web3, service.datatoken_address, consumer_wallet.address, publisher_wallet
    )

    response = initialize_service(
        client,
        asset.did,
        service.id,
        service.type,
        service.datatoken_address,
        consumer_wallet,
        raw_response=True,
    )
    assert "error" in response.json
    assert response.json["error"] == "Asset is not consumable."


def test_initialize_on_asset_with_custom_credentials(
    client, publisher_wallet, consumer_wallet, web3
):
    asset = get_dataset_ddo_with_denied_consumer(
        client, publisher_wallet, consumer_wallet.address
    )

    service = asset.get_service_by_type(ServiceType.ACCESS)

    mint_100_datatokens(
        web3, service.datatoken_address, consumer_wallet.address, publisher_wallet
    )

    response = initialize_service(
        client,
        asset.did,
        service.id,
        service.type,
        service.datatoken_address,
        consumer_wallet,
        raw_response=True,
    )
    assert "error" in response.json
    assert (
        response.json["error"]
        == f"Error: Access to asset {asset.did} was denied with code: ConsumableCodes.CREDENTIAL_IN_DENY_LIST."
    )


def test_download_multiple_files(client, publisher_wallet, consumer_wallet, web3):
    asset = get_dataset_ddo_with_multiple_files(client, publisher_wallet)
    service = asset.get_service_by_type(ServiceType.ACCESS)

    mint_100_datatokens(
        web3, service.datatoken_address, consumer_wallet.address, publisher_wallet
    )

    tx_id, _ = start_order(
        web3,
        service.datatoken_address,
        consumer_wallet.address,
        to_wei(1),
        service.index,
        BLACK_HOLE_ADDRESS,
        BLACK_HOLE_ADDRESS,
        0,
        consumer_wallet,
    )

    # Consume using url index and auth token
    # (let the provider do the decryption)
    payload = {
        "documentId": asset.did,
        "serviceId": service.id,
        "serviceType": service.type,
        "dataToken": service.datatoken_address,
        "consumerAddress": consumer_wallet.address,
        "signature": generate_auth_token(consumer_wallet),
        "transferTxId": tx_id,
        "fileIndex": 0,
    }
    download_endpoint = BaseURLs.SERVICES_URL + "/download"
    response = client.get(download_endpoint, query_string=payload)
    assert response.status_code == 200, f"{response.data}"

    payload["signature"] = generate_auth_token(consumer_wallet)
    payload["fileIndex"] = 1
    download_endpoint = BaseURLs.SERVICES_URL + "/download"
    response = client.get(download_endpoint, query_string=payload)
    assert response.status_code == 200, f"{response.data}"

    payload["signature"] = generate_auth_token(consumer_wallet)
    payload["fileIndex"] = 2
    download_endpoint = BaseURLs.SERVICES_URL + "/download"
    response = client.get(download_endpoint, query_string=payload)
    assert response.status_code == 200, f"{response.data}"

# 0.011
# 110000000000000000
from brownie import Lottery, accounts, network, config, exceptions
from scripts.deploy_lottery import (
    deploy_lottery,
    get_account,
    fund_with_link,
    get_contract,
)
from web3 import Web3
import pytest

from scripts.util import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_contract


def test_get_entrance_fee():

    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()

    # Act
    entrance_fee = lottery.getEntranceFee()
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    # Assert
    # 2000 eth /ud

    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():
    # Arrange
    lottery = deploy_lottery()

    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter():
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})

    # Act
    lottery.enter(
        {"from": account, "value": lottery.getEntranceFee() + 10000000000000000}
    )

    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter(
        {"from": account, "value": lottery.getEntranceFee() + 10000000000000000}
    )
    fund_with_link(lottery)
    lottery.endLottery({"from": account})

    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter(
        {"from": account, "value": lottery.getEntranceFee() + 10000000000000000}
    )
    lottery.enter(
        {
            "from": get_account(index=1),
            "value": lottery.getEntranceFee() + 10000000000000000,
        }
    )
    lottery.enter(
        {
            "from": get_account(index=2),
            "value": lottery.getEntranceFee() + 10000000000000000,
        }
    )

    fund_with_link(lottery)

    tx = lottery.endLottery({"from": account})
    request_id = tx.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )

    # 777 % 3 == 0
    starting_balance = account.balance()
    balance_of_lottery = lottery.balance()

    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance + balance_of_lottery

from server.src.td_server.services.economy import EconomyManager


# Test suite for the EconomyManager
def test_initial_gold_and_lives():
    """Verify that initial values for lives and gold are set correctly."""
    # Arrange: Create an instance with initial values.
    economy = EconomyManager(initial_lives=20, initial_gold=100)

    # Act & Assert: Check the values for both players.
    assert economy.get_lives("A") == 20
    assert economy.get_gold("A") == 100
    assert economy.get_lives("B") == 20
    assert economy.get_gold("B") == 100


def test_spend_gold_success():
    """Test a successful gold expenditure."""
    # Arrange
    economy = EconomyManager(initial_lives=20, initial_gold=100)

    # Act: Player A spends 30 gold.
    success = economy.spend_gold("A", 30)

    # Assert: The operation should succeed, and the player's gold should decrease.
    assert success is True
    assert economy.get_gold("A") == 70
    assert economy.get_gold("B") == 100  # Player B's gold should remain untouched.


def test_spend_gold_insufficient_funds():
    """Test an attempt to spend more gold than available."""
    # Arrange
    economy = EconomyManager(initial_lives=20, initial_gold=100)

    # Act: Player A attempts to spend 110 gold.
    success = economy.spend_gold("A", 110)

    # Assert: The operation should fail, and the gold balance should be unchanged.
    assert success is False
    assert economy.get_gold("A") == 100


def test_lose_lives():
    """Test the process of losing lives."""
    # Arrange
    economy = EconomyManager(initial_lives=20, initial_gold=100)

    # Act: Player B loses 5 lives.
    economy.lose_lives("B", 5)

    # Assert
    assert economy.get_lives("B") == 15
    assert economy.get_lives("A") == 20  # Player A's lives should remain untouched.


def test_lives_cannot_go_below_zero():
    """Ensure that the number of lives cannot become negative."""
    # Arrange
    economy = EconomyManager(initial_lives=20, initial_gold=100)

    # Act: Player A loses 30 lives, which is more than they have.
    economy.lose_lives("A", 30)

    # Assert
    assert economy.get_lives("A") == 0

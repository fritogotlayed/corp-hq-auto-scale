from corp_hq_auto_scale import log

import mock


@mock.patch('corp_hq_auto_scale.log.logging.StreamHandler')
def test_setup(mock_stream_handler):
    # Arrange
    expected_stream_handler = mock.MagicMock()
    mock_logger = mock.MagicMock()
    mock_stream_handler.return_value = expected_stream_handler

    # Act
    log.setup(mock_logger)

    # Assert
    mock_logger.addHandler.assert_called_once_with(expected_stream_handler)

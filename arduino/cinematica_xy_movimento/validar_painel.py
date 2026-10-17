"""Testes logicos do painel, sem conectar ao Uno nem abrir janela.
Executar: python validar_painel.py (requer pyserial, como o painel).
Nao valida eventos reais do teclado, USB ou seguranca mecanica.
"""
import unittest
from unittest.mock import Mock, patch
import painel_espaco as ui


class TestPainel(unittest.TestCase):
    def setUp(self):
        self.p = ui.Painel.__new__(ui.Painel)
        self.p.root, self.p.area = Mock(), Mock()
        self.p.root.focus_get.return_value = self.p.area
        self.p.held = self.p.require_release = False
        self.p.ready_at = self.p.next_heartbeat = 0
        self.p.port = Mock(out_waiting=0, in_waiting=0)
        self.p.port.write.side_effect = len
        self.p.port.read.return_value = b""
        self.p.append = Mock()
        self.physical = patch.object(ui, "physical_space", return_value=None)
        self.physical.start()
        self.addCleanup(self.physical.stop)

    def test_press_release(self):
        self.p.press()
        self.assertTrue(self.p.held)
        self.p.port.write.assert_called_with(ui.RUN)
        self.p.release()
        self.assertFalse(self.p.held)
        self.p.port.write.assert_called_with(ui.PAUSE)

    def test_repeat_does_not_queue(self):
        self.p.press()
        self.p.press()
        self.assertEqual(self.p.port.write.call_count, 1)

    def test_wrong_focus_cannot_allow(self):
        self.p.root.focus_get.return_value = Mock()
        self.p.press()
        self.assertFalse(self.p.held)
        self.p.port.write.assert_not_called()

    def test_lost_focus_pauses(self):
        self.p.press()
        self.p.root.focus_get.return_value = Mock()
        self.p.tick()
        self.assertFalse(self.p.held)
        self.p.port.write.assert_called_with(ui.PAUSE)

    def test_lost_release_detected_on_windows(self):
        self.p.press()
        with patch.object(ui, "physical_space", return_value=False):
            self.p.tick()
        self.assertFalse(self.p.held)
        self.p.port.write.assert_called_with(ui.PAUSE)

    def test_focus_change_requires_key_up(self):
        self.p.press()
        with patch.object(ui, "physical_space", return_value=True):
            self.p.release()
            self.p.press()
        self.assertFalse(self.p.held)
        with patch.object(ui, "physical_space", return_value=False):
            self.p.tick()
        self.p.press()
        self.assertTrue(self.p.held)

    def test_no_background_heartbeat(self):
        self.p.tick()
        self.p.port.write.assert_not_called()

    def test_leave_removes_control_focus(self):
        self.p.press()
        self.p.leave()
        self.assertFalse(self.p.held)
        self.p.root.focus_set.assert_called_once()
        self.p.port.write.assert_called_with(ui.PAUSE)

    def test_congested_usb_does_not_queue_run(self):
        old_port = self.p.port
        old_port.out_waiting = 5
        self.p.press()
        self.assertFalse(self.p.held)
        self.assertIsNone(self.p.port)
        self.assertNotIn(unittest.mock.call(ui.RUN), old_port.write.call_args_list)

    def test_send_mover_always_releases(self):
        self.p.press()
        self.p.command = Mock()
        self.p.command.get.return_value = "mover"
        self.p.send_command()
        self.assertFalse(self.p.held)
        self.assertEqual(self.p.port.write.call_args_list[-2:],
                         [unittest.mock.call(ui.PAUSE), unittest.mock.call(b"mover\n")])


if __name__ == "__main__":
    unittest.main(verbosity=2)

from sverchok.utils.testing import EmptyTreeTestCase

import sverchok.core.events as ev


class SverchokEventTest(EmptyTreeTestCase):

    def test_sverchek_event_set(self):
        sv_event1 = ev.SverchokEvent(ev.SverchokEventsTypes.add_node, self.tree)
        sv_event2 = ev.SverchokEvent(ev.SverchokEventsTypes.add_node)
        sv_event3 = ev.SverchokEvent(ev.SverchokEventsTypes.add_node, self.tree)
        self.assertEqual(len({sv_event1, sv_event2, sv_event3}), 2)

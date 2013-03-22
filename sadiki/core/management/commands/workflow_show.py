# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from sadiki.core.models import STATUS_CHOICES


class Command(BaseCommand):
    help = "Creates workflow dot graph"
    args = "[out.png]"

    def handle(self, filename=None, **options):
        try:
            from pydot import Dot, Edge, Node
        except ImportError:
            raise CommandError("need pydot python module ( apt-get install python-pydot )")

        graph = Dot()

        for status, description in STATUS_CHOICES:
            graph.add_node(Node(
                'status-%s' % status,
                label='"%s (%s)"' %
                    (description.encode('utf-8'), status))
            )

        from sadiki.core.workflow import workflow
        for transition_index in workflow.available_transitions():
            transition = workflow.get_transition_by_index(transition_index)
            graph.add_edge(Edge(
                'status-%s'% transition.src,
                'status-%s' % transition.dst,
                label='"%s (%s)"' % (transition.comment.encode('utf-8'), transition.index),
                style='solid' if transition.required_permissions else 'dashed',
            ))

        if filename:
            graph.write_png(filename)
        else:
            print graph.to_string()

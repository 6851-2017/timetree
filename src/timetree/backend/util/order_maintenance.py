from .linked_list import LinkedList
from .linked_list import LinkedNode
from .linked_list import SizeTrackingListMixin
from .linked_list import SizeTrackingNodeMixin


class QuadraticLabelerNodeMixin(LinkedNode):
    __slots__ = ('label',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = None

    def insert(self, prev):
        # We now search up layers until we hit a valid range to relabel things
        # Note that this is carefully constructed so that each node's label
        # is set at most once, to allow for subclasses to intercept it properly

        # Insert yourself
        super().insert(prev)

        # Initialize the search at layer 0
        layer = 0
        max_nodes = 1

        # Find the candidate label range, with width 1
        if prev.is_head:
            min_label = 1
        else:
            assert isinstance(prev, QuadraticLabelerNodeMixin)
            min_label = prev.label + 1
        max_label = min_label

        # Find the range of nodes to be inserted
        first_node, last_node = self, self
        num_nodes = 1

        while True:
            # Expand the range as far as we can
            while first_node.prev.is_node and first_node.prev.label >= min_label:
                first_node = first_node.prev
                num_nodes += 1
            while last_node.next.is_node and last_node.next.label <= max_label:
                last_node = last_node.next
                num_nodes += 1

            # If we're sparse enough, just exit
            if num_nodes <= max_nodes:
                break

            # Increment the layer number, update bounds
            layer += 1
            # Nodes is 2^layer
            max_nodes = 1 << layer
            # Label range has size 4^layer
            mask = (1 << (2 * layer))-1
            min_label &= ~mask
            max_label |= mask

        # Now, relabel all nodes in the range to have the right behavior
        cur_node = first_node
        for i in range(min_label, max_label+1, (max_label-min_label+1)//max_nodes):
            cur_node.label = i
            if cur_node is last_node:
                break
            cur_node = cur_node.next

    def remove(self):
        super().remove()
        self.label = None


class QuadraticLabelerListMixin(LinkedList):
    __slots__ = ()


class ExponentialLabelerNodeMixin(LinkedNode):
    __slots__ = ('label',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = None

    class LabelError(ValueError):
        pass

    def insert(self, prev):
        super().insert(prev)

        prev_label = self.prev.label if self.prev.is_node else 0
        next_label = self.next.label if self.next.is_node else (1 << self.next.capacity)

        if next_label - prev_label == 1:
            raise ExponentialLabelerNodeMixin.LabelError('Out of labels')

        self.label = (next_label - prev_label) // 2

    def remove(self):
        super().remove()
        self.label = None


class ExponentialLabelerListMixin(LinkedList):
    __slots__ = ('capacity',)

    def __init__(self, *args, capacity, **kwargs):
        super().__init__(*args, **kwargs)
        self.capacity = max(capacity, 31)  # Might as well use 32-bits


class FastLabelerNodeMixin(SizeTrackingNodeMixin):
    __slots__ = ('lower',)

    class LowerNode(ExponentialLabelerNodeMixin):
        __slots__ = ('node', 'upper',)

        def __init__(self, node, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.node = node
            self.upper = None

        def insert(self, prev):
            super().insert(prev)
            self.upper = prev.upper

        def remove(self):
            super().remove()
            self.upper = None

    class LowerList(ExponentialLabelerListMixin):
        __slots__ = ('upper',)

        def __init__(self, upper, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.upper = upper
            upper.lower_list = self

    class UpperNode(QuadraticLabelerNodeMixin):
        __slots__ = ('lower_list')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.lower_list = None

    class UpperList(QuadraticLabelerListMixin):
        __slots__ = ()

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.lower = FastLabelerNodeMixin.LowerNode(self)

    def insert(self, prev):
        super().insert(prev)
        try:
            self.lower.insert(prev.lower)
        except ExponentialLabelerNodeMixin.LabelError:
            # We have to reflow things, so grab the list of lowers
            cur_upper = self.lower.upper
            lower_list = cur_upper.lower_list
            cur_upper.lower_list = None  # Remove the old list

            # The new capacity is log(list_size), and the size is half of that
            new_capacity = self.head.size.bit_length()
            new_size = new_capacity // 2

            assert lower_list.next.is_node, "Lower list should contain at least ourself"

            while True:
                cur_lower = FastLabelerNodeMixin.LowerList(cur_upper, capacity=new_capacity)

                for i in range(new_size):
                    if lower_list.next.is_head:
                        break

                    new_lower = lower_list.next
                    new_lower.remove()
                    new_lower.insert(cur_lower)
                    cur_lower = new_lower

                if lower_list.next.is_head:
                    break

                # Prepare a new upper node
                new_upper = FastLabelerNodeMixin.UpperNode()
                new_upper.insert(cur_upper)
                cur_upper = new_upper

    def remove(self):
        super().remove()
        self.lower.remove()

    @property
    def label(self):
        result = (self.lower.upper.label, self.lower.label)
        return result


class FastLabelerListMixin(SizeTrackingListMixin):
    __slots__ = ('lower',)

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        upper = FastLabelerNodeMixin.UpperList()
        upper_node = FastLabelerNodeMixin.UpperNode()
        upper.prepend(upper_node)
        self.lower = FastLabelerNodeMixin.LowerList(upper_node, capacity=31)

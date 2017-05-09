"""Kd-tree for nearest neighbours queries.

This implementation currently runs faster than SciPy's KDTree but is often
slower than a brute-force approach in Hienoi's use cases, killing the primary
purpose for such a data structure. Still, it is left here as an educational
resource.
"""

import collections
import heapq
import itertools
import sys

import numpy

from hienoi._dynamicarray import DynamicArray


if sys.version_info[0] == 2:
    _range = xrange
    _zip = itertools.izip
else:
    _range = range
    _zip = zip

_heappushpop = heapq.heappushpop
_heappush = heapq.heappush
_npmax = numpy.maximum


_INITIAL_NEIGHBOURS_CAPACITY = 32


class KDTree(object):
    """K-d tree.

    Nodes are stored contiguously in memory.
    """

    def __init__(self, data, bucket_size=128):
        if bucket_size < 1:
            raise ValueError("A minimum bucket size of 1 is expected.")

        self._data = data
        self._n, self._k = self._data.shape
        self._nodes = None
        self._buckets = []
        self._bucket_size = bucket_size

        self._node_dtype = numpy.dtype([
            ('size', numpy.intp),
            ('bucket', numpy.intp),
            ('lower_bounds', (numpy.float_, self._k)),
            ('upper_bounds', (numpy.float_, self._k)),
        ])
        self._neighbour_dtype = numpy.dtype([
            ('squared_distance', numpy.float_),
            ('index', numpy.intp),
        ])

        self._build()

    def search(self, point, count, radius, sort):
        """Retrieve the neighbours to a point."""
        if count is None:
            count = self._n
        elif count < 1:
            return numpy.empty(0, dtype=self._neighbour_dtype)

        if radius is None:
            radius = numpy.inf
        elif radius < 0.0:
            return numpy.empty(0, dtype=self._neighbour_dtype)

        point = numpy.asarray(point, dtype=numpy.float_)
        if count >= self._n:
            return self._search_all_within_radius(point, radius, sort)
        else:
            return self._search_k_nearests(point, count, radius, sort)

    def _build(self):
        """Build the k-d tree."""
        data = self._data
        buckets = self._buckets
        bucket_size = self._bucket_size

        # First pass: build the tree using a DFS ordering.
        nodes = []
        parents = []
        i = 0
        stack = collections.deque(((numpy.arange(self._n), None),))
        while stack:
            indices, parent = stack.popleft()
            points = data[indices]
            lower_bounds = numpy.amin(points, axis=0)
            upper_bounds = numpy.amax(points, axis=0)
            if len(points) <= bucket_size:
                bucket = len(buckets)
                buckets.append(indices)
            else:
                bucket = -1

                # Split the longest side of the bounds.
                side_lengths = upper_bounds - lower_bounds
                split_axis = numpy.argmax(side_lengths)
                split_location = (lower_bounds[split_axis]
                                  + upper_bounds[split_axis]) / 2.0
                axis_data = points[:, split_axis]
                left_indices = indices[
                    numpy.nonzero(axis_data <= split_location)[0]]
                right_indices = indices[
                    numpy.nonzero(axis_data > split_location)[0]]
                stack.appendleft((right_indices, i))
                stack.appendleft((left_indices, i))

            size = 1
            nodes.append((size, bucket, lower_bounds, upper_bounds))
            parents.append(parent)
            i += 1

        # Second pass: set the 'size' attribute for each node in the tree.
        # Iterate over the nodes in reverse order to perform a bottom-up
        # traversal where the size of each node is added to the size of its
        # parent.
        self._nodes = numpy.array(nodes, dtype=self._node_dtype)
        node_sizes = self._nodes['size']
        for i in reversed(_range(1, len(self._nodes))):
            node_sizes[parents[i]] += node_sizes[i]

    def _search_k_nearests(self, point, count, radius, sort):
        """Search the nearest points within a radius."""
        data = self._data
        nodes = self._nodes
        buckets = self._buckets

        node_sizes = nodes['size']
        node_buckets = nodes['bucket']
        node_lower_bounds = nodes['lower_bounds']
        node_upper_bounds = nodes['upper_bounds']

        # A max heap would be appropriate to store the nearest points found,
        # alas Python only provides a min heap as part of the `heapq` module.
        # As a hacky workaround, nearest distances are negated.
        nearests = []
        dist_limit = radius ** 2

        pt_root_dist = _pt_to_node_near_dist(
            point, node_lower_bounds[0], node_upper_bounds[0])
        stack = collections.deque(((0, pt_root_dist),))
        while stack:
            i, pt_node_dist = stack.popleft()
            if pt_node_dist > dist_limit:
                # The node's bounds are too far, skip this branch.
                pass
            elif node_sizes[i] == 1:
                # This is a leaf node, see if there are any nearest points.
                indices = buckets[node_buckets[i]]
                points = data[indices]
                dists = numpy.sum(
                    (point[numpy.newaxis, :] - points) ** 2, axis=-1)
                for j, dist in _zip(indices, dists):
                    if dist < dist_limit:
                        if len(nearests) >= count:
                            dist_limit = -_heappushpop(nearests, (-dist, j))[0]
                        else:
                            _heappush(nearests, (-dist, j))
            else:
                # Inspect the child nodes.
                left_node_idx = i + 1
                right_node_idx = i + 1 + node_sizes[left_node_idx]
                pt_left_node_dist = _pt_to_node_near_dist(
                    point, node_lower_bounds[left_node_idx],
                    node_upper_bounds[left_node_idx])
                pt_right_node_dist = _pt_to_node_near_dist(
                    point, node_lower_bounds[right_node_idx],
                    node_upper_bounds[right_node_idx])
                if pt_left_node_dist <= pt_right_node_dist:
                    stack.appendleft((right_node_idx, pt_right_node_dist))
                    stack.appendleft((left_node_idx, pt_left_node_dist))
                else:
                    stack.appendleft((left_node_idx, pt_left_node_dist))
                    stack.appendleft((right_node_idx, pt_right_node_dist))

        out = numpy.array(nearests, dtype=self._neighbour_dtype)
        out['squared_distance'] *= -1.0
        if sort:
            # Here is the biggest performance killer. Runs in a single thread.
            out.sort(order='squared_distance')

        return out

    def _search_all_within_radius(self, point, radius, sort):
        """Search all the points within a radius."""
        data = self._data
        nodes = self._nodes
        buckets = self._buckets

        node_sizes = nodes['size']
        node_buckets = nodes['bucket']
        node_lower_bounds = nodes['lower_bounds']
        node_upper_bounds = nodes['upper_bounds']

        radius **= 2
        neighbours = DynamicArray(_INITIAL_NEIGHBOURS_CAPACITY,
                                  self._neighbour_dtype)

        pt_root_dist = _pt_to_node_near_dist(
            point, node_lower_bounds[0], node_upper_bounds[0])
        stack = collections.deque(((0, pt_root_dist),))
        while stack:
            i, pt_node_near_dist = stack.popleft()
            if pt_node_near_dist > radius:
                # The node's bounds are too far, skip this branch.
                pass
            elif (_pt_to_node_far_dist(
                    point, node_lower_bounds[i], node_upper_bounds[i])
                  <= radius):
                # The node's bounds are within the radius, recursively retrieve
                # all the points.
                children = nodes[i:i + node_sizes[i]]
                leaves = numpy.extract(children['size'] == 1, children)
                count = sum(len(buckets[bucket])
                            for bucket in leaves['bucket'])
                j = len(neighbours)
                neighbours.resize(j + count)
                neighbours.data['squared_distance'][j:] = numpy.nan
                for bucket in leaves['bucket']:
                    indices = buckets[bucket]
                    count = len(indices)
                    neighbours.data['index'][j:j + count] = indices
                    j += count
            elif node_sizes[i] == 1:
                # This is a leaf node, see if there are any points within the
                # radius.
                indices = buckets[node_buckets[i]]
                points = data[indices]
                dists = numpy.sum(
                    (point[numpy.newaxis, :] - points) ** 2, axis=-1)
                is_within = dists <= radius
                j = len(neighbours)
                neighbours.resize(j + numpy.sum(is_within))
                neighbours.data['squared_distance'][j:] = dists[is_within]
                neighbours.data['index'][j:] = indices[is_within]
            else:
                # Inspect the child nodes.
                left_node_idx = i + 1
                right_node_idx = i + 1 + node_sizes[left_node_idx]
                pt_left_node_dist = _pt_to_node_near_dist(
                    point, node_lower_bounds[left_node_idx],
                    node_upper_bounds[left_node_idx])
                pt_right_node_dist = _pt_to_node_near_dist(
                    point, node_lower_bounds[right_node_idx],
                    node_upper_bounds[right_node_idx])
                if pt_left_node_dist <= pt_right_node_dist:
                    stack.appendleft((right_node_idx, pt_right_node_dist))
                    stack.appendleft((left_node_idx, pt_left_node_dist))
                else:
                    stack.appendleft((left_node_idx, pt_left_node_dist))
                    stack.appendleft((right_node_idx, pt_right_node_dist))

        # Compute all the distances.
        is_nan = numpy.isnan(neighbours.data['squared_distance'])
        indices = neighbours.data['index'][numpy.nonzero(is_nan)]
        points = data[indices]
        dists = numpy.sum((point[numpy.newaxis, :] - points) ** 2, axis=-1)
        neighbours.data['squared_distance'][is_nan] = dists

        if sort:
            # Here is the biggest performance killer. Runs in a single thread.
            neighbours.data.sort(order='squared_distance')

        return neighbours.data


def _pt_to_node_near_dist(point, lower_bounds, upper_bounds):
    return numpy.sum(
        _npmax(0.0, _npmax(point - upper_bounds, lower_bounds - point))
        ** 2)


def _pt_to_node_far_dist(point, lower_bounds, upper_bounds):
    return numpy.sum(
        _npmax(0.0, _npmax(upper_bounds - point, point - lower_bounds))
        ** 2)

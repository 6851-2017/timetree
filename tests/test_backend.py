import pytest


@pytest.mark.persistence_none
def test_any_backend(backend):
    head = backend.branch()
    vnode = head.new_node()
    vnode.set('f', 5)
    assert vnode.get('f') == 5
    vnode2 = head.new_node()
    vnode.set('ptr', vnode2)
    vnode2.set('ptr', vnode)
    assert vnode.get('ptr') == vnode2
    assert vnode2.get('ptr') == vnode


@pytest.mark.persistence_partial
def test_partial_backend(backend):
    head = backend.branch()
    vnode = head.new_node()
    vnode.set('f', 5)
    assert vnode.get('f') == 5
    vnode2 = head.new_node()
    vnode.set('ptr', vnode2)
    vnode2.set('ptr', vnode)
    assert vnode.get('ptr') == vnode2
    assert vnode2.get('ptr') == vnode

    # test commit
    commit, [old_vnode] = backend.commit([vnode])
    vnode.set('f', 8)
    assert vnode.get('f') == 8
    assert old_vnode.get('f') == 5
    vnode2.set('ptr', None)
    old_vnode2 = old_vnode.get('ptr')
    assert old_vnode == old_vnode2.get('ptr')

@pytest.mark.persistence_partial
def test_partial_backend_many_commits(backend):
    head = backend.branch()
    root = head.new_node()
    vnode = head.new_node()
    root.set('ptr', vnode)

    commits = []
    for i in range(1000):
        vnode.set('val', i)
        commits.append(backend.commit([root, vnode])[1])

    for i in range(1000):
        assert commits[i][0].get('ptr').get('val') == i
        assert commits[i][1].get('val') == i

@pytest.mark.persistence_partial
def test_partial_backend_chain_split(backend):
    head = backend.branch()
    vnode_a = head.new_node()
    vnode_b = head.new_node()
    vnode_c = head.new_node()
    vnode_d = head.new_node()

    commits = []
    for i in range(1000):
        vnode_a.set('val', ('a', i))
        vnode_b.set('val', ('b', i))
        vnode_c.set('val', ('c', i))
        vnode_d.set('val', ('d', i))
        vnode_a.set('a', vnode_a)
        vnode_a.set('b', vnode_b)
        vnode_a.set('c', vnode_c)
        vnode_a.set('d', vnode_d)
        vnode_b.set('a', vnode_a)
        vnode_b.set('b', vnode_b)
        vnode_b.set('c', vnode_c)
        vnode_b.set('d', vnode_d)
        vnode_c.set('a', vnode_a)
        vnode_c.set('b', vnode_b)
        vnode_c.set('c', vnode_c)
        vnode_c.set('d', vnode_d)
        vnode_d.set('a', vnode_a)
        vnode_d.set('b', vnode_b)
        vnode_d.set('c', vnode_c)
        vnode_d.set('d', vnode_d)
        commits.append(backend.commit([vnode_a, vnode_b, vnode_c, vnode_d])[1])

    for i in range(1000):
        vnode_a, vnode_b, vnode_c, vnode_d = commits[i]
        assert vnode_a.get('val') == ('a', i)
        assert vnode_b.get('val') == ('b', i)
        assert vnode_c.get('val') == ('c', i)
        assert vnode_d.get('val') == ('d', i)
        for vnode in vnode_a, vnode_b, vnode_c, vnode_d:
            assert vnode.get('a') == vnode_a
            assert vnode.get('b') == vnode_b
            assert vnode.get('c') == vnode_c
            assert vnode.get('d') == vnode_d

@pytest.mark.persistence_partial
def test_partial_backend_keyerror(backend):
    head = backend.branch()
    vnode = head.new_node()
    commits = []

    with pytest.raises(KeyError):
        vnode.get('val')
    commits.append(vnode.commit())

    vnode.set('val', 1)
    assert vnode.get('val') == 1
    commits.append(vnode.commit())

    vnode.delete('val')
    with pytest.raises(KeyError):
        vnode.get('val')
    commits.append(vnode.commit())

    with pytest.raises(KeyError):
        commits[0].get('val')
    assert commits[1].get('val') == 1
    with pytest.raises(KeyError):
        commits[2].get('val')


@pytest.mark.persistence_confluent
def test_confluent_backend(backend):
    head = backend.branch()
    vnode = head.new_node()
    vnode.set('f', 5)
    assert vnode.get('f') == 5
    # test commit
    commit, [old_vnode] = backend.commit([vnode])
    vnode.set('f', 8)
    assert vnode.get('f') == 8
    assert old_vnode.get('f') == 5
    # test full
    head2, [vnode2] = backend.branch([old_vnode])
    vnode2.set('f', 9)
    assert vnode.get('f') == 8
    assert old_vnode.get('f') == 5
    assert vnode2.get('f') == 9
    # test confluence
    commit2, [vnode3] = backend.commit([vnode])
    head, [new_vnode, new_vnode3] = backend.branch([old_vnode, vnode3])
    assert new_vnode.get('f') == 5
    assert new_vnode3.get('f') == 8

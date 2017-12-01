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

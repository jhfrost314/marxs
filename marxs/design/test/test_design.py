import numpy as np
from scipy.stats import kstest

from ..rowland import RowlandTorus, GratingArrayStructure, find_radius_of_photon_shell
from ...optics.base import OpticalElement
from ...source import ConstantPointSource, FixedPointing
from ...optics import MarxMirror

def parametrictorus(R, r, theta, phi):
    x = (R + r * np.cos(theta)) * np.cos(phi)
    y = (R + r * np.cos(theta)) * np.sin(phi)
    z = r * np.sin(theta)
    return x, y, z

def test_radius_of_photon_shell():
    mysource = ConstantPointSource((30., 30.), 1., 1.)
    photons = mysource.generate_photons(1000)
    mypointing = FixedPointing(coords=(30, 30.))
    photons = mypointing.process_photons(photons)
    marxm = MarxMirror('./marxs/optics/hrma.par', position=np.array([0., 0, 0]))
    photons = marxm.process_photons(photons)
    r1, r2 = find_radius_of_photon_shell(photons, 3, 9e4)
    assert abs(r1 - 5380.) < 10.
    assert abs(r2 - 5495.) < 10.


def test_torus():
    '''Test the torus equation for a set of points.

    Importantly, we use a parametric description of the torus here, which is
    different from the actual implementation.
    '''
    R = 2.
    r = 1.

    angle = np.arange(0, 2 * np.pi, 0.1)
    phi, theta = np.meshgrid(angle, angle)
    phi = phi.flatten()
    theta = theta.flatten()
    x, y, z = parametrictorus(R, r, theta, phi)
    mytorus = RowlandTorus(R=R, r=r)

    assert np.allclose(mytorus.quartic(x, y, z), 0.)

def test_torus_normal():
    '''Compare the analytic normal with a numeric result.

    The test computes a vector along the torus for small d_theta
    and d_phi. Both of those should be perpendicular to the normal.
    '''
    R = 2.
    r = 1.

    angle = np.arange(0, 2 * np.pi, 0.1)
    phi, theta = np.meshgrid(angle, angle)
    phi = phi.flatten()
    theta = theta.flatten()
    x, y, z = parametrictorus(R, r, theta, phi)
    xt1, yt1, zt1 = parametrictorus(R, r, theta + 0.001, phi)
    xp1, yp1, zp1 = parametrictorus(R, r, theta, phi + 0.001)
    xt0, yt0, zt0 = parametrictorus(R, r, theta - 0.001, phi)
    xp0, yp0, zp0 = parametrictorus(R, r, theta, phi + 0.001)

    mytorus = RowlandTorus(R=R, r=r)
    vec_normal = np.vstack(mytorus.normal(x, y, z))

    vec_delta_theta = np.vstack([xt1 - xt0, yt1 - yt0, zt1 - zt0])
    vec_delta_phi = np.vstack([xp1 - xp0, yp1 - yp0, zp1 - zp0])

    assert np.allclose(np.einsum('ij,ij->j', vec_normal, vec_delta_theta), 0.)
    assert np.allclose(np.einsum('ij,ij->j', vec_normal, vec_delta_phi), 0.)

def test_GratingArrayStructure():
    '''Check a GAS for consistency

    The expected numbers for this one are hand-checked and plotted and thus
    can be taken as known-good to prevent regressions later.
    '''
    myrowland = RowlandTorus(10000., 10000.)
    class mock_facet(OpticalElement):
        pass
    gas = GratingArrayStructure(myrowland, 30., [10000., 20000.], [300., 600.], phi=[-0.2*np.pi, 0.2*np.pi], facetclass=mock_facet)
    assert gas.max_facets_on_arc(300.) == 12
    angles = gas.distribute_facets_on_arc(315.) % (2. * np.pi)
    # This is a wrap-around case. Hard to test in general, but here I know the numbers
    assert np.alltrue((angles < 0.2 * np.pi) | (angles > 1.8 * np.pi))
    assert gas.max_facets_on_radius() == 10
    assert np.all(gas.distribute_facets_on_radius() == np.arange(315., 600., 30.))
    assert len(gas.facet_pos) == 177
    center = gas.calc_ideal_center()
    assert center[1] == 0
    assert center[2] == (300. + 600.) / 2.
    assert 2e4 - center[0] < 20.  # R_rowland >> r_gas  -> center close to R_rowland
    # fig, axes = plt.subplots(2,2)
    # for elem in [[axes[0, 0], 0, 1], [axes[0, 1], 0, 2], [axes[1, 0], 1, 2]]:
    #     for f in gas.facet_pos:
    #         elem[0].plot(f[elem[1],3], f[elem[2],3], 's')
    # plt.show()  # or move mouse in window or something.

    # There is a test missing here that the rotational part works correctly.
    # I just cannot think of a good way to check that right now.

    # Check that initially all uncertainties are 0
    for i in range(len(gas.facet_pos)):
        assert np.allclose(gas.facet_pos[i], gas.facets[i].pos4d)

def test_GratingArrayStructure_2pi():
    '''test that delta_phi = 2 pi means "full circle" and not 0
    '''
    myrowland = RowlandTorus(10000., 10000.)
    class mock_facet(OpticalElement):
        pass
    gas = GratingArrayStructure(myrowland, 30., [10000., 20000.], [300., 600.], phi=[0, 2*np.pi], facetclass=mock_facet)
    assert gas.max_facets_on_arc(300.) > 10
    n = len(gas.facet_pos)
    yz = np.empty((n, 2))
    for i, p in enumerate(gas.facet_pos):
        yz[i, :] = p[1:3, 3]
    phi = np.arctan2(yz[:, 1], yz[:, 0])
    ks, pvalue = kstest((phi + np.pi) / (2 * np.pi), 'uniform')
    assert pvalue > 0.3  # It's not exactly uniform because of finite size of facets.

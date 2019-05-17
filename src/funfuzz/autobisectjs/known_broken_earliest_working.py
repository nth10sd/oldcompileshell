# coding=utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Known broken changeset ranges of SpiderMonkey are specified in this file.
"""

import platform

from pkg_resources import parse_version


def hgrange(first_bad, first_good):  # pylint: disable=missing-param-doc,missing-return-doc,missing-return-type-doc
    # pylint: disable=missing-type-doc
    """Like "first_bad::first_good", but includes branches/csets that never got the first_good fix."""
    # NB: mercurial's descendants(x) includes x
    # So this revset expression includes first_bad, but does not include first_good.
    # NB: hg log -r "(descendants(id(badddddd)) - descendants(id(baddddddd)))" happens to return the empty set,
    # like we want"
    return f"(descendants(id({first_bad}))-descendants(id({first_good})))"


def known_broken_ranges(options):  # pylint: disable=missing-param-doc,missing-return-doc,missing-return-type-doc
    # pylint: disable=missing-type-doc
    """Return a list of revsets corresponding to known-busted revisions."""
    # Paste numbers into: https://hg.mozilla.org/mozilla-central/rev/<number> to get hgweb link.
    # To add to the list:
    # - (1) will tell you when the brokenness started
    # - (1) <python executable> -m funfuzz.autobisectjs --compilationFailedLabel=bad -e FAILINGREV
    # - (2) will tell you when the brokenness ended
    # - (2) <python executable> -m funfuzz.autobisectjs --compilationFailedLabel=bad -s FAILINGREV

    # ANCIENT FIXME: It might make sense to avoid (or note) these in checkBlameParents.

    skips = [
        hgrange("4c72627cfc6c", "926f80f2c5cc"),  # Fx60, broken spidermonkey
        hgrange("1fb7ddfad86d", "5202cfbf8d60"),  # Fx63, broken spidermonkey
        hgrange("aae4f349fa58", "c5fbbf959e23"),  # Fx64, broken spidermonkey
        hgrange("f611bc50d11c", "39d0c50a2209"),  # Fx66, broken spidermonkey
    ]

    if platform.system() == "Darwin":
        skips.extend([
            hgrange("3d0236f985f8", "32cef42080b1"),  # Fx68, see bug 1544418
        ])

    if platform.system() == "Linux":
        skips.extend([
            # Failure specific to GCC 5 (and probably earlier) - supposedly works on GCC 6
            hgrange("e94dceac8090", "516c01f62d84"),  # Fx56-57, see bug 1386011
        ])
        if platform.machine() == "aarch64":
            skips.extend([
                hgrange("e8bb22053e65", "999757e9e5a5"),  # Fx54, see bug 1336344
            ])
        if not options.disableProfiling:
            skips.extend([
                # To bypass the following month-long breakage, use "--disable-profiling"
                hgrange("aa1da5ed8a07", "5a03382283ae"),  # Fx54-55, see bug 1339190
            ])

    if not options.enableDbg:
        skips.extend([
            hgrange("c5561749c1c6", "f4c15a88c937"),  # Fx58-59, broken opt builds w/ --enable-gczeal
            hgrange("247e265373eb", "e4aa68e2a85b"),  # Fx66, broken opt builds w/ --enable-gczeal
        ])

    if options.enableMoreDeterministic:
        skips.extend([
            hgrange("427b854cdb1c", "4c4e45853808"),  # Fx68, see bug 1542980
        ])

    if options.enableSimulatorArm32:
        skips.extend([
            hgrange("284002382c21", "05669ce25b03"),  # Fx57-61, broken 32-bit ARM-simulator builds
        ])

    return skips


def earliest_known_working_rev(options, flags, skip_revs):  # pylint: disable=missing-param-doc,missing-return-doc
    # pylint: disable=missing-return-type-doc,missing-type-doc,too-many-branches,too-complex,too-many-statements
    """Return a revset which evaluates to the first revision of the shell that compiles with |options|
    and runs jsfunfuzz successfully with |flags|."""
    # Only support at least Mac OS X 10.13
    assert (not platform.system() == "Darwin") or (parse_version(platform.mac_ver()[0]) >= parse_version("10.13"))

    cpu_count_flag = False
    for entry in flags:  # flags is a list of flags, and the option must exactly match.
        if "--cpu-count=" in entry:
            cpu_count_flag = True

    required = []

    # These should be in descending order, or bisection will break at earlier changesets.
    if "--enable-experimental-fields" in flags:  # 1st w/--enable-experimental-fields, see bug 1529758
        required.append("7a1ad6647c22bd34a6c70e67dc26e5b83f71cea4")  # m-c 463705 Fx67
    if set(["--wasm-compiler=none", "--wasm-compiler=baseline+ion", "--wasm-compiler=baseline",
            "--wasm-compiler=ion"]).intersection(flags):  # 1st w/--wasm-compiler=none/<other options>, see bug 1509441
        required.append("48dc14f79fb0a51ca796257a4179fe6f16b71b14")  # m-c 455252 Fx66
    if "--more-compartments" in flags:  # 1st w/--more-compartments, see bug 1518753
        required.append("450b8f0cbb4e494b399ebcf23a33b8d9cb883245")  # m-c 453627 Fx66
    if "--no-streams" in flags:  # 1st w/ working --no-streams, see bug 1501734
        required.append("c6a8b4d451afa922c4838bd202749c7e131cf05e")  # m-c 442977 Fx65
    if platform.system() == "Windows" and options.enable32:  # 1st w/ working 32-bit Windows builds, see bug 1483835
        required.append("577ffed9f102439db47afebcef95bbaaa2e04c93")  # m-c 432608 Fx63
    if platform.system() == "Windows":  # 1st w/ working Windows builds with a recent Win10 SDK, see bug 1462616
        required.append("c085e1b32fb9bbdb00360bfb0a1057d20a752f4c")  # m-c 419184 Fx62
    if "--wasm-gc" in flags:  # 1st w/--wasm-gc, see bug 1445272
        required.append("302befe7689abad94a75f66ded82d5e71b558dc4")  # m-c 413255 Fx61
    if "--nursery-strings=on" in flags or \
            "--nursery-strings=off" in flags:  # 1st w/--nursery-strings=on, see bug 903519
        required.append("321c29f4850882a2f0220a4dc041c53992c47992")  # m-c 406115 Fx60
    if "--spectre-mitigations=on" in flags or \
            "--spectre-mitigations=off" in flags:  # 1st w/--spectre-mitigations=on, see bug 1430053
        required.append("a98f615965d73f6462924188fc2b1f2a620337bb")  # m-c 399868 Fx59
    if "--test-wasm-await-tier2" in flags:  # 1st w/--test-wasm-await-tier2, see bug 1388785
        required.append("b1dc87a94262c1bf2747d2bf560e21af5deb3174")  # m-c 387188 Fx58
    if platform.system() == "Darwin":  # 1st w/ successful Xcode 9 builds, see bug 1366564
        required.append("e2ecf684f49e9a6f6d072c289df68ef679968c4c")  # m-c 383101 Fx58
    if cpu_count_flag:  # 1st w/--cpu-count=<NUM>, see bug 1206770
        required.append("1b55231e6628e70f0c2ee2b2cb40a1e9861ac4b4")  # m-c 380023 Fx57
    # 1st w/ revised template literals, see bug 1317375
    required.append("bb868860dfc35876d2d9c421c037c75a4fb9b3d2")  # m-c 330353 Fx53

    return f"first(({common_descendants(required)}) - ({skip_revs}))"


def common_descendants(revs):  # pylint: disable=missing-docstring,missing-return-doc,missing-return-type-doc
    return " and ".join(f"descendants({r})" for r in revs)

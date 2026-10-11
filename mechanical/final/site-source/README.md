# Quadcuber gravity-return R4

Current routes: dist/index.html (full 882-part 3D preview), dist/integrated-assembly.html (unified209-step illustrated reader), dist/integrated-operation.html (secondary operation stages), dist/integrated-support.html (legacy standalone150-part reader).

The immutable R1 support loses two working lock pins and gains exactly20 approved lever/stop parts. Paused horizontal+6 is excluded. All normal whole-machine states contain882 parts. Tray endpoint40.8mm. No latch/band or automatic upper hold.

Build: python3 build_integrated_revision.py. Geometry and full guide are supplied by sibling lift-feasibility/integrated-revision during authoring, or parentfolder in the delivered site-source layout. Current tests: python3 test_integrated_bundle.py; python3 viewer-dom-validation.py; node --test unified-reader.test.cjs viewer-workbench-ui.test.cjs; node --test gravity-step-pose.test.cjs; native11MPD validation via validate_integrated_models.cjs. Original historical tests remain for their original fixtures; those are not current acceptance.

Current UI uses exact per-step geometry_records, including lower U installation pose, with explicit reset when returning to normal view. Browser pixels remain unverified where browser execution is blocked; realLDraw parse/link/source checks and PDF pixelQA are separate.

Physical assembly, strength, gravityreturn, damping/impact, grip, hand separation and poweredcontrol remain unaccepted. No firmware change.

R4 closes the inherited missing R–B base corner: two 7L beams become15L, one32526 L-beam and four2780 pins are added. Base64, all four39790 floor frames unchanged, zero71709. The20 lever bodies and support geometry are unchanged. Closed topology alone is not a physical stiffness qualification.

UI workbench: two primary routes, viewport-sized canvas, visible named views/zoom/reset/fullscreen, native-image sizing, previous/next/phase navigation and original/new-part highlighting. All209 original guide pages remain exact;128 nonempty pages provide rotatable local geometry (36base+92support),81 use diagrams. The original arms remain prebuilt inputs. Compact step child ordinals map through geometry_records[j].index1, never through whole-machine indices. Offline viewer has four local pages with explicit local imageRoot.

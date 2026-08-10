# CHANGELOG


## v2.2.0 (2026-08-10)

### Bug Fixes

- **53**: Handle batch operations more gracefully
  ([`df38e7e`](https://github.com/bmcivor/taigun/commit/df38e7e3c3cc3cccc8a9fed8f152d1585d4486c5))

While making it more robust.

- **57**: Load side car on dry run to make it accurate
  ([`e78072e`](https://github.com/bmcivor/taigun/commit/e78072e9ba6a094e26d6c4091ccc6ef14fbfa68e))

### Chores

- **101**: Add ruff, mypy, and pytest-cov with config
  ([`8ce278b`](https://github.com/bmcivor/taigun/commit/8ce278bd1101c7e10dd1a070e0ce6084920f0e95))

- **102**: Add scripts and compose service for lint runs
  ([`26278ce`](https://github.com/bmcivor/taigun/commit/26278ce1786159cd9348f0bf5f52afd3660b5add))

- **103**: Backfill ruff violations and format
  ([`b61524f`](https://github.com/bmcivor/taigun/commit/b61524f4af778afeb396c403e6b19081960e777e))

- **104**: Backfill mypy errors and fixes
  ([`f6f9200`](https://github.com/bmcivor/taigun/commit/f6f9200cf9ee4e0a8bd5b77bfd6b2f3f9ef3b342))

- **105**: Remove LLM hallucinations about coverage reports
  ([`1998dca`](https://github.com/bmcivor/taigun/commit/1998dca521de4f57305197f0ab1f8f84e9ed5476))

None of this was part of the spec... so that was fun to tear out.

- **105**: Update Jenkinsfile stages
  ([`557c574`](https://github.com/bmcivor/taigun/commit/557c5743a824f70ec179994e62dc40496e680e23))

- **106**: Document contributing to the app
  ([`d9299b5`](https://github.com/bmcivor/taigun/commit/d9299b5c7b7b18b36bb29447ee387a89d4df755c))


## v2.1.1 (2026-07-27)

### Bug Fixes

- Ensure that the version of taigun tracked in uv is kept aligned
  ([`4977faf`](https://github.com/bmcivor/taigun/commit/4977faf2c2be76e66a378e7e5ce6abc543fdb066))

- Mask profile password from repr output
  ([`e0ac3e1`](https://github.com/bmcivor/taigun/commit/e0ac3e19e70d08bf8a6c000333b5a9faa489f416))

This isn't that big of a deal, but we should be following safe practices of not just blasting out
  somebodies password in prints or logs, in the future. If that ever becomes a thing.

- Streamline update methodolody to common helpers
  ([`013f17e`](https://github.com/bmcivor/taigun/commit/013f17e31e4684c10c82b099e15aa9c1bf40639d))

- Update is_closed status handling for story
  ([`f0b3d33`](https://github.com/bmcivor/taigun/commit/f0b3d3358c0be1aa2c74be8f2bb192943d2fbbb2))

- Use --no-cache during release process
  ([`6469887`](https://github.com/bmcivor/taigun/commit/6469887ac7d865686bde9eac194a3913020ce887))

### Chores

- Update skill knowledge for AI
  ([`4775fde`](https://github.com/bmcivor/taigun/commit/4775fde6a002cc4efa49952bd9ca1f167cdb294e))


## v2.1.0 (2026-07-22)

### Chores

- Add in basic explanation and format structure
  ([`56763d6`](https://github.com/bmcivor/taigun/commit/56763d62d07f56636ec9453ec75ace8fcb787de2))

- Add in cli reference
  ([`da79813`](https://github.com/bmcivor/taigun/commit/da79813448866b42abb00c421762b59b6d3dfe98))

- Add in configuration reference
  ([`7775d9a`](https://github.com/bmcivor/taigun/commit/7775d9a338f607b3698a4c43a687241878ea9742))

- Add in docs Jenkinsfile step to verify docs build
  ([`3929e05`](https://github.com/bmcivor/taigun/commit/3929e05c5bc78ec38801cd63627694ebc206c90e))

- Add in getting started tutorial pages
  ([`8008f0f`](https://github.com/bmcivor/taigun/commit/8008f0fe62126ee8d9bf74cb6d7bfb607cf94019))

- Add in guide for managing project level
  ([`b59ae03`](https://github.com/bmcivor/taigun/commit/b59ae0319d0c0e85e3d3adf9dade093155b655d7))

- Add in managing multiple profiles
  ([`9fa25f1`](https://github.com/bmcivor/taigun/commit/9fa25f1303d812ee8c877577c670c9dd724a3ff8))

- Add in milestones documentation
  ([`fb3314f`](https://github.com/bmcivor/taigun/commit/fb3314fac24eb5a1242d0f7692ab21428153a569))

- Add in specific docs build stage for CI pipeline
  ([`207d8e7`](https://github.com/bmcivor/taigun/commit/207d8e7ae0165dde7279578db5f306bd98411662))

- Add in state file reference sheet
  ([`ed2e2e3`](https://github.com/bmcivor/taigun/commit/ed2e2e322cbfded160e7204065967b1e56465ed2))

- Add in ticket organisation guide
  ([`a410d16`](https://github.com/bmcivor/taigun/commit/a410d1641f6e82a480e80bd138c13211b3bc9fb0))

- Add in updating tickets guide
  ([`3303f00`](https://github.com/bmcivor/taigun/commit/3303f00b1b882980263a8810573ce219c9e34c27))

- Clean up existing documentation structure
  ([`98c8fd8`](https://github.com/bmcivor/taigun/commit/98c8fd8f1b5b297c850a4aaedb3374b2386f354d))

To prepare for the incoming new, fully detailed structure.

- Clean up some claude mess in test assertions
  ([`ee6da5b`](https://github.com/bmcivor/taigun/commit/ee6da5b090c0057b702e975adf9eafe027bfc775))

- Initial finalisation stage of documentation
  ([`8dffb61`](https://github.com/bmcivor/taigun/commit/8dffb6141bcbca5855de9ab6a33b7e3a90df8ce3))

- Remove duplicated frontmatter explanation on index
  ([`c8dd7ad`](https://github.com/bmcivor/taigun/commit/c8dd7ad70e4921a47e72ac7483184b97a9a4de36))

- Remove untracked files and exclusions
  ([`752c195`](https://github.com/bmcivor/taigun/commit/752c195e1bfc313b4af7a213136858ef37c5840f))

We don't need them anymore.


## v2.0.0 (2026-07-14)

### Bug Fixes

- Update planning status doc
  ([`f0620f1`](https://github.com/bmcivor/taigun/commit/f0620f10ef04fc338c7c3f535ddf3891c4942025))

- Update uv.lock version to match repo
  ([`0a14801`](https://github.com/bmcivor/taigun/commit/0a14801dab1c55e778c6277bf6f0db79530caeaa))

- **037**: Stop hard failures on status resolver attempts
  ([`24f9fef`](https://github.com/bmcivor/taigun/commit/24f9fefc35022aafbab826ee1fc3eb22d4ee3f1d))

### Chores

- Update mistake in plan for tickets refactoring
  ([`24895fd`](https://github.com/bmcivor/taigun/commit/24895fd51287d2bf1f2c38168bf6b1999d5841a0))

### Features

- **039**: Remove tickets from repo
  ([`6d17c06`](https://github.com/bmcivor/taigun/commit/6d17c0629c92ccc3d34eb16f16760efff46e28cd))

Time to start using this tool in a more production like manner.

It's not really a normal practice to have tickets on disk, committed to the repo. So moving it to a
  more communal, user managed dir format where all repos will have their status tracked.

- **040**: Migrate local skill knowledge to tool repo
  ([`9299ff4`](https://github.com/bmcivor/taigun/commit/9299ff49cbd145e749de56f282ec15b07ca0f077))


## v1.1.0 (2026-07-14)

### Bug Fixes

- **027**: Clean up docs in tests and document usage
  ([`ec4b473`](https://github.com/bmcivor/taigun/commit/ec4b473d82d5cb88dc9b17d2c7061b3599bea9ba))

- **033**: Add in sidecar for updating existing tickets
  ([`46a6558`](https://github.com/bmcivor/taigun/commit/46a655822a3a2a064e36e672253e4d02979aa3e9))

This is a bit of a bad design to be honest. Caught about halfway through that this was
  unnecessarily, over complicated as a design.

But we can roll with it for now.

- **036**: Fix sidecare default path so it is more robust
  ([`03714d9`](https://github.com/bmcivor/taigun/commit/03714d9c872161d3a0d6acf80460aaff12387ab9))

### Chores

- General docs and planning update
  ([`f0e9a94`](https://github.com/bmcivor/taigun/commit/f0e9a945a837cb7d833f5ad8b948192b1406b470))

- Update assignees on existing tickets
  ([`83b4c32`](https://github.com/bmcivor/taigun/commit/83b4c32cd0cc7d8a1b24695c3101b82aca42c5b1))

- Update docs with decision to postpone insane claude design for CI
  ([`8d7932c`](https://github.com/bmcivor/taigun/commit/8d7932ca6cde9240b5d5d9dbc825aff69f755341))

- Update documentation statuses and workflow definitions
  ([`48af6b6`](https://github.com/bmcivor/taigun/commit/48af6b6461313288b0fe9401eba86cca102a5cf0))

- Update uv lock file version to match correct version
  ([`9c83959`](https://github.com/bmcivor/taigun/commit/9c83959345e17a80b5040be8e3caa3afefa74ea5))

- **926**: Clean up overzealous monkeypatching in connections
  ([`64af59c`](https://github.com/bmcivor/taigun/commit/64af59cb2377ed0b48bc5dc85d4cf24913bab83d))

### Features

- Add in planning for follow up hardening of app
  ([`f16764d`](https://github.com/bmcivor/taigun/commit/f16764dabbd909f2a44ce6536e82cff214951fcf))

- Basic plan on hardening and update strategies
  ([`f3f1f19`](https://github.com/bmcivor/taigun/commit/f3f1f193d6ee39721f7434a98af9c607e9925911))

- Update planning for updating mechanisms
  ([`275a48f`](https://github.com/bmcivor/taigun/commit/275a48f3b86f8ddb7caac7398a95c1488fd47c8d))

- **028**: Add in milestone writer
  ([`0acec79`](https://github.com/bmcivor/taigun/commit/0acec791c3e1ef50233e460ef0cd7d1370ddcc36))

- **031**: Apply various persistent bugs from dogfooding finds
  ([`0d695a8`](https://github.com/bmcivor/taigun/commit/0d695a86be3225f0aa3763f1724afd988fd851fc))

- **032**: Complete ADR for update workflow
  ([`6b59fbd`](https://github.com/bmcivor/taigun/commit/6b59fbdb442d70d2c77a72946e98ede4cb7384cb))

- **034**: Add in update and upsert functionality to all db types
  ([`975e4f7`](https://github.com/bmcivor/taigun/commit/975e4f77b7c49fa2bf5ce6a2575a4e10fd2aafac))

- **035**: Update projects and milestones functionality
  ([`6426ef4`](https://github.com/bmcivor/taigun/commit/6426ef445f659bbe4f65d1b0d0abc4bfc2b38db6))

- **30**: Include investigation results from dog fooding
  ([`04c84c6`](https://github.com/bmcivor/taigun/commit/04c84c62e01d8f8a1a5f4da4b13e6689b5f23baf))


## v1.0.0 (2026-05-15)

### Bug Fixes

- Minor updates to finalize successful taigun runs
  ([`984eb04`](https://github.com/bmcivor/taigun/commit/984eb042854f90606b45c44cb86c9e3e8c4fade7))

### Features

- First attempt at rewriting ticket structure
  ([`aa37a8f`](https://github.com/bmcivor/taigun/commit/aa37a8f135b71ed70594c783806ab9aa3cdcf1fe))


## v0.2.0 (2026-05-14)

### Bug Fixes

- **022**: Add in basic docker harness to use real db connections
  ([`cc0d009`](https://github.com/bmcivor/taigun/commit/cc0d009d4f9fe9d13eca53c6babf471f34ac79c4))

- **022**: Remove insane mocking and use real infrastructure for testing
  ([`087bffa`](https://github.com/bmcivor/taigun/commit/087bffac153bcb4107ad942ac6ab163d34b0cec3))

- **022**: Update test coverage
  ([`b1e38ef`](https://github.com/bmcivor/taigun/commit/b1e38ef0ef185719c6f6de4de43c0b54d156c683))

### Chores

- **022**: Refactory tests structure for cli
  ([`ab0b8ca`](https://github.com/bmcivor/taigun/commit/ab0b8ca769b9ad5cffdfd564aa275ae86da4e1fb))

### Features

- Add in updated plan to fix the mess of this design
  ([`bc4c35a`](https://github.com/bmcivor/taigun/commit/bc4c35a307016917d6997a9eb8016ba1aa3115c6))

- Update ticket statuses
  ([`bddbe55`](https://github.com/bmcivor/taigun/commit/bddbe554e6f235e6d951a729fccc4d197f292aac))

- **020**: Add in project cli command opt
  ([`5ec88e7`](https://github.com/bmcivor/taigun/commit/5ec88e7e64147cad39eef08ca918966279994a4b))

- **021**: Add in basic real taiga test hardness back and db
  ([`82d1f30`](https://github.com/bmcivor/taigun/commit/82d1f300c9b41a58afbeeb32f0d23484aaea159d))

- **023**: Address xfails tests after moving to real test harness
  ([`43bc1e1`](https://github.com/bmcivor/taigun/commit/43bc1e147024bebc10230bf4cd713483dcc30efa))

- **024**: Setup jenkins pipeline to actually run properly
  ([`4bcb024`](https://github.com/bmcivor/taigun/commit/4bcb02497e944557ff522079de8d0148b4384091))


## v0.1.0 (2026-05-02)

### Bug Fixes

- Set uv cache dir for release process
  ([`cc2e416`](https://github.com/bmcivor/taigun/commit/cc2e416f1900e2fff1eb5a3127cf9598203e8569))

- Update uv lock file properly
  ([`b06ac61`](https://github.com/bmcivor/taigun/commit/b06ac6106be6c169e57c7b37ca2d7d21b8bde587))

- **007**: Refactor parsers out of insane structure
  ([`a29094a`](https://github.com/bmcivor/taigun/commit/a29094a5d13078c34eda87db184273757a68c02a))

- **009**: Add in missing test scripting for resolver
  ([`b9b7479`](https://github.com/bmcivor/taigun/commit/b9b74793a28b3ed60e933f998b27af0c38d719a9))

- **013**: Add in missing task writer tests
  ([`179b750`](https://github.com/bmcivor/taigun/commit/179b75098e7c6212f6cd6588ad82628dff0d60dd))

- **015**: Add in missing tests script for cli configure
  ([`644b57a`](https://github.com/bmcivor/taigun/commit/644b57a9d338b1fd16ee730f7baa735cb837f1fb))

- **018**: Move to setuptools
  ([`a8e2614`](https://github.com/bmcivor/taigun/commit/a8e26142e275c965358b89dc545f24d355ce0511))

and kill off this dumb AI slop idea

- **018**: Update venv handling to be non root
  ([`b911b16`](https://github.com/bmcivor/taigun/commit/b911b16e318db94eecef694bdef6c58013ed48cf))

### Chores

- Refactory the config scripting into OOP practices
  ([`102ac80`](https://github.com/bmcivor/taigun/commit/102ac80db2d86c9272a1c9a489d185f01abe3f9c))

- Remove some of the substantial mocking in tests
  ([`f1d98aa`](https://github.com/bmcivor/taigun/commit/f1d98aa0790d6bf5760968ad5de74c2d48b8a864))

- Update docs status
  ([`a368348`](https://github.com/bmcivor/taigun/commit/a3683486e4ee7f2d01f9748528eddab93115c7ed))

- Update documentation and README
  ([`3da5566`](https://github.com/bmcivor/taigun/commit/3da5566c64d585b8d80d90e45862b57a5d2a1ba6))

- Update project status and tickets
  ([`d2d59b3`](https://github.com/bmcivor/taigun/commit/d2d59b3108fbacc72f7ee6d74c7d820f4ab92f90))

- **014**: Create base writer class for all writers to work from
  ([`3f18ceb`](https://github.com/bmcivor/taigun/commit/3f18ceb626603b9ceca1cc19671577f7019bba80))

- **016**: Code clean up through tests to make them consistent
  ([`0e5db5d`](https://github.com/bmcivor/taigun/commit/0e5db5d1f28683b4d19afb1992f618b0c79e4f56))

- **016**: Incluse missing testing infra and scope
  ([`cd4047a`](https://github.com/bmcivor/taigun/commit/cd4047a56864d1459dd3d6c57238565292682e55))

### Features

- Add in basic python package scaffolding
  ([`a5f8a11`](https://github.com/bmcivor/taigun/commit/a5f8a112fa499ff555a664d2b286ac0f557fc834))

- Add in basic testing infra
  ([`95cb21a`](https://github.com/bmcivor/taigun/commit/95cb21a924537c51ea8cb399d9a1acfb19c46ff4))

- Add in new progress update sheet
  ([`9132a9a`](https://github.com/bmcivor/taigun/commit/9132a9a15ed302e4429dbd4f075da714f4a04222))

- Add in planning documentation with ticket breakdown
  ([`2d92073`](https://github.com/bmcivor/taigun/commit/2d9207379bc296ba86e35196f5641634fd728324))

- Fix more dumb mistakes made by claude
  ([`0f3b3f0`](https://github.com/bmcivor/taigun/commit/0f3b3f0baee15ad46291e5de655189b89ca15844))

- Progress docs update
  ([`78c7f1a`](https://github.com/bmcivor/taigun/commit/78c7f1a2a69d4e2be42619e0cf5bc1221cf4f726))

- Update epic 1 as complete
  ([`82e61ca`](https://github.com/bmcivor/taigun/commit/82e61cae9396e143cfbfa6e2d447593c6d84e0f2))

- Update progress docs to close off epic 2
  ([`e585f60`](https://github.com/bmcivor/taigun/commit/e585f604ae0013ef7bffbc0f8cba54e305fff057))

- **004**: Add in config loading module and basic test framework
  ([`95bcb7c`](https://github.com/bmcivor/taigun/commit/95bcb7c82d06a2cef1b1d2e2a8a39a9b2bc49851))

- **005**: Finish up modelling
  ([`a16fd36`](https://github.com/bmcivor/taigun/commit/a16fd3663ae6b7f906353a62b6f69c39a236d1b0))

- **006**: Setup frontmatter parser for md
  ([`0e56046`](https://github.com/bmcivor/taigun/commit/0e560464bf52ae39b09529f844a4b33a3e0a51d2))

- **007**: Add in body parser and refactor structure
  ([`f6ef4c1`](https://github.com/bmcivor/taigun/commit/f6ef4c1639d35b6f0a18bab122ae1832fe706ade))

- **008**: Add in db resolver on modelling
  ([`082034b`](https://github.com/bmcivor/taigun/commit/082034b18cca4805dc215c35d6675a144d947d73))

- **008**: Setup basic db connection handler
  ([`3d03950`](https://github.com/bmcivor/taigun/commit/3d0395023e8b912596eff1e4a260d2c8145a9f31))

- **010**: Add in ref allocation handler
  ([`79d33ad`](https://github.com/bmcivor/taigun/commit/79d33ad3166821a0e260a9386e6141663a09acd0))

Includes a pretty big refactor, cleaning up the mess of a structure that things were becoming.

- **011**: Add om story writer for stories
  ([`cb66923`](https://github.com/bmcivor/taigun/commit/cb66923b53d96f2c1216932997da2193763e32af))

- **013**: Add in task writer
  ([`41ffcb6`](https://github.com/bmcivor/taigun/commit/41ffcb6ea8013feeb0c6dfb949f8720715ad5264))

- **014**: Add in epic writer
  ([`1fc2313`](https://github.com/bmcivor/taigun/commit/1fc231394f172c2ca5fa8da857e410cda151f717))

- **015**: Add in configure option to cli
  ([`3bec371`](https://github.com/bmcivor/taigun/commit/3bec3715cda8d3fe6e93be93b784decd91d77d71))

- **016**: First run at push cli command option
  ([`0a76953`](https://github.com/bmcivor/taigun/commit/0a76953c691e84ce17e1045f8c0fb4c9d7870025))

- **017**: Add in list option to cli
  ([`40bf438`](https://github.com/bmcivor/taigun/commit/40bf438a800ecd6c0b555fdca5e9bc84dba79d36))

- **018**: Add in pinned dependencies and versioning tooling
  ([`6fef2fb`](https://github.com/bmcivor/taigun/commit/6fef2fb84971e25f6ffa120e8651fff6e519884b))

- **018**: Add in release scripting and tooling
  ([`d34d3de`](https://github.com/bmcivor/taigun/commit/d34d3def64dd199195e3e5d9548e6a3e4d9c0173))

- **018**: Make package publishable
  ([`4bb63a8`](https://github.com/bmcivor/taigun/commit/4bb63a8d9ccb3cbcb5a8bb9bc187209be7025d92))

def run(plan):
	requirement_artifact = plan.upload_files(
		src='./requirements.txt',
	)

	plan.add_service(
		"hn-data-puller",
		config=ServiceConfig(
			"python:3.11.5-bullseye",
		),
		files={"/": requirement_artifact}
	)

	#plan.exec("hn-data-puller",
	#	recipe=ExecRecipe([
	#		"pip install " + requirement_artifact.
	#	])
	#)

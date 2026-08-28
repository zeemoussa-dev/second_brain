"""Pipeline entity -- a recurring job's own stage breakdown, rendered as
a worker node on the Agents Map. See pipeline.py for the shape (Pipeline
+ PipelineStep), pipeline_manager.py for the PipelineManager (methods
not yet wired -- scaffolding only). NOT the same folder as
app/business/pipelines/ -- that one holds the real pipeline execution
scripts (email_capture_pipeline.py, email_pull.py,
librarian_housekeeping.py, raw_message_capture.py), a pre-existing
package unrelated to this entity/manager split; don't confuse the two."""

# D02 plan: mock deployment

Run the existing portable application on the reference host with PostgreSQL, RabbitMQ,
dispatcher, API, and mock worker. Prove the API-served browser flow, persistence,
playback/seek, versioning, cancellation, and ordinary restart using test-owned
data. Keep this profile available after real-provider activation.

The prior D02 result on VM `<verification-host-address>` remains valid for that machine only. D02
must be re-run on the reference host before claiming a complete deployment there.

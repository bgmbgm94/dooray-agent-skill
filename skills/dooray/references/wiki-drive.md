# Wiki and drive

Public evidence for wiki routes: [Dooray Go SDK wiki](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/wiki). The shared client uses personal token authentication; permissions vary by resource. List and inspect first, then request authorization for any update.

Drive routes need separate public evidence and mock tests before enabling write operations. A public SDK's coverage of wiki uploads must not be mistaken for Drive API coverage. File downloads need filename/path validation; uploads must never forward personal authorization headers across an HTTP redirect to another host.

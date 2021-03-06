# booksApp - A microservice arch template

#### My Sample Event-Driven Architecture:

Running on...

* a MySQL `AWS RDS` DB
* a `AWS ES` ElasticSearch query engine & `AWS SQS` broker
  * great Command/Query Responsibility Separation!
* **lightweight `k8s`/`Docker`orchestration for `AWS EKS` / `EC2`**

<img src="vagrant_scripts/EDA_Diagram.png" alt="Final k8s Architecture">


<hr>

### Bundled with...

#### 2 independently scalable microservices:

1. bookService
2. customerService

* each running NodeJS / Express API
* handle biz & logic concerns
* Integrated w/`AWS SQS`, `RDS`, & `ES`

#### 2 BFFs (backend-for-frontends)

1. bookBFF
2. customerBFF

* each running a Python server
* handle header parsing, auth, and response transformations
  * (on a user-client basis — ie. different responses for Desktop / Mobile)

#### & 1 Circuit Breaker (for an external service)

1. reccCircuitBreaker

* Sets a 3 second timeout for calls to the service and returns error codes appropriately
  * `504` - Timeout | `503` - Open Circuit | `204` - Not Found | `200` - Success

<hr>

#### k8s Deployment

Config files for k8s deployment are provided at the top-level project directory.

1. Apply the k8s config with: `kubectl apply -f circuitBreakerConfig.yaml -f bookConfig.yaml -f customerConfig.yaml`
   * Each container has a **5 second liveness check**
   * The books services have 2 replicas, while customers have 1
2. See all services / pods: `kubectl get all -n book-app`

**Other Helpful Commands****

1. See Container Logs: `kubectl logs -n book-app <POD ID> <CONTAINER NAME>`
2. SSH into Pod: `kubectl exec -it <POD ID> -n book-app -- bash`
3. Describe Pod: `kubectl describe pods -n book-app <POD ID>`
4. Restart Deployment (ie. after updating some container): `kubectl rollout restart deployment <DEPLOYMENT NAME> -n book-app`

##### Additional IAC / *Infrastructure as Code*

* All the services can be deployed via Docker (Dockerfiles provided in each respective directory):
  * See the [setup script](vagrant_scripts/vmSetup.sh) for help with docker deployment
* Setting up a Dev & Test environment (in a VM):
  * A `Vagrantfile` & `/vagrant_scripts/` are provided for provisioning *both*
    * update the Vagrantfile to use whichever script you'd like
  * Install `Vagrant` & `VirtualBox`
  * run `vagrant up` to start the VM
  * run `vagrant ssh` to enter the VM
* Test scripts are provided in `/tests/`:
  * see the [setup script](vagrant_scripts/vmSetup.sh) for help running it

##### Final k8s Setup:

<img src="vagrant_scripts/final_k8s_setup.png" height="100%" alt="Final k8s Architecture">

### mk

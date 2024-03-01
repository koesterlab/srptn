from common.data import DataStore


class S3DataStore(DataStore):
    # TODO use policies to restrict access to objects based on owner who is logged in and performs the action
    # https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html
    # https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html
    #
    # TODO add method to DataStore that returns an access control widget (None for FSDataStore)
    # TODO add page that allows to modify datasets
    # TODO add page that allows to modify analyses
    ...
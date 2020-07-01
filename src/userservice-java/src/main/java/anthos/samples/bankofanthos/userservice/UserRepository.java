package anthos.samples.bankofanthos.userservice;

import org.springframework.data.repository.CrudRepository;

/**
 * The Spring repository interface which allows for performing CRUD operations on User records.
 */
public interface UserRepository extends CrudRepository<User, Long> {

  User findByUsername(String username);

}

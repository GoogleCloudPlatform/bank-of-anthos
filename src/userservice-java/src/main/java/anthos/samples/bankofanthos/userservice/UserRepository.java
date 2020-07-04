package anthos.samples.bankofanthos.userservice;

import org.springframework.data.repository.CrudRepository;

/**
 * The Spring repository interface which allows for performing CRUD operations on User records.
 */
public interface UserRepository extends CrudRepository<User, Long> {

  /** Finds the User in the database with the specified {@code username}. */
  User findFirstByUsername(String username);
}

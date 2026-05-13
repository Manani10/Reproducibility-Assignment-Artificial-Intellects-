(define (domain test)
  (:predicates (at_start) (at_goal))

  (:action up
    :precondition (at_start)
    :effect (and (not (at_start)) (at_goal))
  )

  (:action right
    :precondition (at_goal)
    :effect (at_goal)
  )
)